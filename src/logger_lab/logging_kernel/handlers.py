"""
Handler infrastructure: configuring, installing and releasing handlers, the shared
file table, and the log-directory helper.

Every piece here is thread-safe.  Loggers swap handler lists atomically, and every log
file is opened **once per process**: loggers that write to the same path share one
handler, which closes when its last logger lets go.
"""

import logging
import os
import threading
import warnings
import weakref
from collections import Counter
from dataclasses import dataclass, field
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Callable, Iterable, TypeVar

from logger_lab.logging_kernel.constants import DEFAULT_LOG_DIR
from logger_lab.logging_kernel.errors import LogDirectoryError, LogFileClashError, SharedFileSettingsWarning

#: Owner recorded for a file handler requested outside a named logger (a direct factory call).
UNNAMED = "<unnamed>"

#: Any handler type — `configure_handler` hands back the same type it was given.
HandlerT = TypeVar("HandlerT", bound=logging.Handler)


#############################
# Handlers that stay closed #
#############################

class StayClosedMixin(logging.FileHandler):
    """
    Make a file handler drop records after `close()` instead of reopening its file.

    Mix it in *before* the handler class (``class X(StayClosedMixin, RotatingFileHandler)``)
    so its `close`/`emit` run first.

    The stdlib `FileHandler` reopens its file on the next `emit()` after a close.  A
    thread that was mid-record while its logger was rebuilt could otherwise reopen a
    file that was just released — leaking the handle and, on Windows, blocking rotation.
    """

    closed_for_good: bool = False

    def close(self) -> None:
        """Mark the handler closed *before* closing, so no record waiting on its lock reopens the file."""

        self.closed_for_good = True
        super().close()

    def emit(self, record: logging.LogRecord) -> None:
        """Write *record*, or drop it once the handler is closed."""

        if self.closed_for_good:
            return

        super().emit(record)


class SharedFileHandler(StayClosedMixin):
    """`FileHandler` for the ``file`` experiment — shared through the file table, never reopened once closed."""


class SharedRotatingFileHandler(StayClosedMixin, RotatingFileHandler):
    """`RotatingFileHandler` for the ``rotating_file`` experiment — shared, never reopened once closed."""


#####################
# Shared file table #
#####################

@dataclass
class SharedFile:
    """One open log file: its handler, the experiment that opened it, its settings, and who uses it."""

    handler: logging.FileHandler
    kind: str
    settings: dict[str, object]
    owners: Counter[str] = field(default_factory=Counter)


#: Every open log file in the process, keyed by `file_key()`.
SHARED_FILES: dict[str, SharedFile] = {}

#: Handlers logger-lab created (via `configure_handler`) — the only ones it ever closes.
#: Anything else on a logger (pytest's capture handler, a user's own handler) is detached, never closed.
LAB_HANDLERS: "weakref.WeakSet[logging.Handler]" = weakref.WeakSet()

#: Guards ``SHARED_FILES`` and every logger's handler swap — each check-then-change happens under it.
SHARED_FILES_LOCK = threading.RLock()


def file_key(path: Path | str) -> str:
    """Return the table key for *path*: absolute, resolved, and case-normalized on Windows."""

    return os.path.normcase(str(Path(path).resolve()))


def share_file_handler(
    path: Path | str,
    *,
    kind: str,
    settings: dict[str, object],
    open_handler: Callable[[], logging.FileHandler],
    logger_name: str | None = None,
) -> logging.FileHandler:
    """
    Return the one handler for *path*, opening it only if no logger has it open yet.

    File experiments call this instead of constructing a handler, so a file is never
    opened twice.  When *path* is already open:

    * same *kind*, same *settings* → the existing handler is shared;
    * same *kind*, different *settings* → shared with the **first** settings, and a
      `SharedFileSettingsWarning` names what was ignored;
    * different *kind* → `LogFileClashError` — one handler can't be both.

    Exception: if the only logger using *path* is the one asking, it is being rebuilt,
    so a new handler with the new kind/settings replaces the old one.

    Args:
        path:         The log file.
        kind:         The experiment opening it, e.g. ``"FILE"``, ``"ROTATING"``.
        settings:     The handler settings that must agree to share (encoding, sizes).
        open_handler: Builds the handler when the file isn't open yet.
        logger_name:  The logger asking, for ownership and messages.
    Returns:
        The handler for *path* — newly opened or shared.
    Raises:
        `LogFileClashError`: If another logger has *path* open with a different experiment.
    Example::
        handler = share_file_handler(
            log_path, kind="FILE", settings={"encoding": "utf-8"},
            open_handler=lambda: SharedFileHandler(log_path), logger_name=__name__,
        )
    """

    owner = logger_name or UNNAMED
    key = file_key(path)

    with SHARED_FILES_LOCK:
        shared = SHARED_FILES.get(key)

        # Closed outside the table (e.g. handler.close() by hand) — treat as gone.  Not `stream is None`:
        # a rotating handler sets that briefly mid-rollover, and it would open a second handler.
        if shared is not None and getattr(shared.handler, "closed_for_good", False):
            shared = None

        if shared is not None:
            same_config = shared.kind == kind and shared.settings == settings
            rebuilding_alone = owner != UNNAMED and set(shared.owners) == {owner}

            if same_config or not rebuilding_alone:
                if shared.kind != kind:
                    raise LogFileClashError(key, held_by=sorted(shared.owners), held_as=shared.kind,
                                            wanted_by=owner, wanted_as=kind)

                if shared.settings != settings:
                    warnings.warn(SharedFileSettingsWarning(key, kept=shared.settings, ignored=settings,
                                                            owner=owner), stacklevel=2)

                shared.owners[owner] += 1

                return shared.handler

        # Not open yet, or its only logger is rebuilding it differently: open a fresh handler.
        # A replaced handler leaves the table and closes when its logger releases it.
        handler = open_handler()
        SHARED_FILES[key] = SharedFile(handler, kind, dict(settings), Counter({owner: 1}))

        return handler


def release_handler(handler: logging.Handler, logger_name: str | None = None) -> None:
    """
    Release *logger_name*'s use of *handler*, closing it once nobody uses it.

    A shared file handler stays open while any other logger still writes to it.
    Other handlers logger-lab created are closed straight away.  Handlers logger-lab
    did *not* create are left open — they may serve other loggers we know nothing about.

    Args:
        handler:     A handler being removed from a logger.
        logger_name: The logger letting go of it.
    """

    owner = logger_name or UNNAMED

    with SHARED_FILES_LOCK:
        for key, shared in SHARED_FILES.items():
            if shared.handler is handler:
                shared.owners[owner] -= 1

                if shared.owners[owner] <= 0:
                    del shared.owners[owner]

                if shared.owners:
                    return

                del SHARED_FILES[key]
                break

        ours = handler in LAB_HANDLERS

    if ours:
        handler.close()


def install_handlers(logger: logging.Logger, factories: Iterable[Callable[[], list[logging.Handler]]]) -> None:
    """
    Build every handler from *factories*, then put them on *logger* in one atomic swap.

    1. Each factory runs; if one raises, the handlers built so far are released and
       *logger* is left exactly as it was.
    2. ``logger.handlers`` is replaced in a single assignment.  A thread logging at that
       moment finishes its record on the old list — it never sees a half-built one.
    3. The old handlers are released (`release_handler`).

    Args:
        logger:    The logger to (re)configure.
        factories: Zero-argument callables, each returning handlers.
    Example::
        install_handlers(logger, [partial(standard_experiment, logging.INFO)])
    """

    new_handlers: list[logging.Handler] = []

    try:
        for factory in factories:
            new_handlers += factory()

    except BaseException:
        for handler in new_handlers:
            release_handler(handler, logger.name)

        raise

    with SHARED_FILES_LOCK:  # concurrent installs on one logger must not both release the same old list
        old_handlers = logger.handlers
        logger.handlers = new_handlers

    for handler in old_handlers:
        release_handler(handler, logger.name)


# Handler guard
def clear_handlers(logger: logging.Logger) -> None:
    """Detach and release every handler on *logger* in one atomic swap.

    Releasing matters for file handlers: a detached-but-open handler keeps its
    file locked (on Windows, that blocks rotation) and leaks the descriptor.
    A shared file handler stays open while another logger still uses it, and
    handlers logger-lab didn't create are detached but never closed.
    Idempotent — safe to call on a fresh logger.

    Args:
        logger: The logger whose handlers will be removed and released.
    """

    install_handlers(logger, [])


# Experiment skeleton — shared handler configuration
def configure_handler(
    handler: HandlerT,
    level: int,
    formatter: logging.Formatter | None = None
    ) -> HandlerT:
    """Apply *level* and *formatter* to *handler* and return it.

    This is the **shared experiment skeleton**.  Every experiment calls
    this for each handler it creates so the configuration contract is
    enforced in one place:

    1. Set the logging level on the handler.
    2. Attach the formatter (if supplied; Rich handlers manage their own).
    3. Record it as logger-lab's own, so `release_handler` may close it later.

    Args:
        handler:   Any :class:`logging.Handler` subclass.
        level:     Standard :mod:`logging` level constant.
        formatter: Pre-built formatter to attach, or ``None`` for handlers
                   that manage their own formatting (e.g. ``RichHandler``).

    Returns:
        The same *handler* instance, mutated in place, for convenient
        one-liner use inside experiment functions::

            return [_configure_handler(RichHandler(), level)]
    """

    handler.setLevel(level)

    if formatter is not None:
        handler.setFormatter(formatter)

    with SHARED_FILES_LOCK:
        LAB_HANDLERS.add(handler)

    return handler


# File-system helpers
def get_log_dir(path: Path | str = DEFAULT_LOG_DIR) -> Path:
    """
    Ensure the log directory exists and return it as a :class:`~pathlib.Path`.

    Creates the directory (and any missing parents) if it does not exist.
    This is the **single place** where file-based experiments create the
    log directory; neither ``file_experiment`` nor
    ``rotating_file_experiment`` should call :func:`os.makedirs` or
    :meth:`~pathlib.Path.mkdir` directly.

    Args:
        path: Directory path, as a string or `Path`.
              Defaults to ``logs/`` relative to the current working directory.
    Returns:
        The resolved `Path` to the log directory.
    Raises:
        `LogDirectoryError`:
            If the directory cannot be created or accessed (e.g. permission
            denied). The original `OSError` is chained as ``__cause__``.
    Example::
        handler = FileHandler(get_log_dir("var/log/myapp") / "app.log")
    """

    log_dir = Path(path)

    try:
        log_dir.mkdir(parents=True, exist_ok=True)

    except OSError as err:
        raise LogDirectoryError(log_dir, str(err)) from err

    return log_dir
