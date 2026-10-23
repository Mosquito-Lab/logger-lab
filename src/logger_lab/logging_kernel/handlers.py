"""
Handler infrastructure: configuring, installing and releasing handlers, the shared
file table, and the log-directory helper.

Every piece here is thread-safe. Loggers swap handler lists atomically. Every log file is
opened **once per process**, so loggers that write to the same path share one handler. It
closes when its last logger lets go.
"""

import logging
import os
import threading
import time
import warnings
import weakref
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from logging.handlers import BaseRotatingHandler
from pathlib import Path
from collections.abc import Callable, Iterable
from typing import TypeVar

from logger_lab.logging_kernel.constants import DEFAULT_LOG_DIR
from logger_lab.logging_kernel.errors import LogDirectoryError, LogFileClashError, SharedFileSettingsWarning
from logger_lab.logging_kernel.rollover import SizeRule, TimeRule, backup_sort_key

UNNAMED = "<unnamed>"  # Owner recorded for a file handler requested outside a named logger
HandlerT = TypeVar("HandlerT", bound=logging.Handler)  # Any handler type: configure_handler returns what it was given


#################
# File handlers #
#################

class StayClosedMixin(logging.FileHandler):
    """
    Make a file handler drop records after `close()` instead of reopening its file.

    Mix it in *before* the handler class (``class X(StayClosedMixin, BaseRotatingHandler)``)
    so its `close`/`emit` run first.

    The stdlib `FileHandler` reopens its file on the next `emit()` after a close. A
    thread that was mid-record while its logger was rebuilt could otherwise reopen a
    file that was just released. That leaks the handle and, on Windows, blocks rotation.
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


class LabFileHandler(StayClosedMixin, BaseRotatingHandler):
    """
    The one file handler: a plain log file, optionally rolled over by size, on a schedule, or both.

    Shared through the file table (one per path) and never reopened once closed.

    Backup names:

    * size only (``ROTATING``): the stdlib scheme, ``app.log.1`` (newest) … ``app.log.N``;
    * on a schedule (``TIMED``): the period's label, ``app.log.2026-10-22``;
    * both: the label plus a counter, so two size rollovers in one day keep both pieces,
      ``app.log.2026-10-22.1`` and ``app.log.2026-10-22.2``.

    A backup is never overwritten. (The stdlib timed handler deletes a same-named one.)
    *backup_count* is how many backups are kept, and the oldest go first.
    """

    def __init__(
        self,
        filename: Path | str,
        *,
        encoding: str,
        backup_count: int,
        size: SizeRule | None = None,
        schedule: TimeRule | None = None,
    ) -> None:
        """Open *filename* for appending, with the given rollover rules (none means a plain file)."""

        super().__init__(filename, "a", encoding=encoding)
        self.bom_size = len("".encode(encoding))  # Bytes a codec like UTF-16 adds to every encode; the file has one
        self.backup_count = backup_count
        self.size = size
        self.schedule = schedule
        self.period: datetime | None = None
        self.rollover_at: float | None = None

        if schedule is not None:
            # An existing file belongs to the period it was last written in (as the stdlib does).
            started = (schedule.from_timestamp(os.path.getmtime(filename)) if os.path.exists(filename)
                       else schedule.now())
            self.period = schedule.period_start(started)
            self.rollover_at = schedule.to_timestamp(schedule.next_boundary(started))

    def shouldRollover(self, record: logging.LogRecord) -> bool:
        """True when the schedule's boundary has passed, or writing *record* would reach the size."""

        if self.period_ended():
            return True

        if self.size is not None:
            stream = self.stream if self.stream is not None else self._open()
            self.stream = stream
            stream.seek(0, 2)
            position = stream.tell()

            if position == 0:  # Never roll over an empty file, as the stdlib does from 3.13 (gh-116263)
                return False

            return position + self.encoded_size(f"{self.format(record)}{self.terminator}") >= self.size.max_bytes

        return False

    def encoded_size(self, text: str) -> int:
        """
        How many bytes *text* takes in the file, so ``max_bytes`` caps bytes, not characters (KN-39).

        It counts in the file's encoding, with ``os.linesep`` for each newline, because text
        mode writes ``\\r\\n`` on Windows. It leaves out the byte-order mark that some codecs,
        such as UTF-16, add to every encode. The stdlib counts characters, so its cap is approximate.
        """

        data = text.replace("\n", os.linesep).encode(self.encoding or "utf-8", self.errors or "strict")

        return len(data) - self.bom_size

    def doRollover(self) -> None:
        """
        Move the current file to its backup name, prune old backups, and start a fresh file.

        A scheduled period with nothing written makes no backup. The handler just moves on
        to the next period, so an idle day can't push a real backup out of *backup_count*.
        """

        if self.schedule is not None and self.period_ended() and self.is_empty():
            self.start_next_period()
            return

        stream = self.stream

        if stream is not None:
            stream.close()
            self.stream = None

        if self.schedule is None:
            self.roll_numbered()
        else:
            self.roll_labeled()

        self.stream = self._open()

    def roll_numbered(self) -> None:
        """Size-only rollover: shift ``.1`` → ``.2`` …, then the file becomes ``.1`` (the stdlib scheme)."""

        for index in range(self.backup_count - 1, 0, -1):
            source = self.rotation_filename(f"{self.baseFilename}.{index}")
            target = self.rotation_filename(f"{self.baseFilename}.{index + 1}")

            if os.path.exists(source):
                if os.path.exists(target):
                    os.remove(target)

                os.rename(source, target)

        target = self.rotation_filename(f"{self.baseFilename}.1")

        if os.path.exists(target):
            os.remove(target)

        self.rotate(self.baseFilename, target)

    def roll_labeled(self) -> None:
        """Scheduled rollover: name the backup after its period (plus a counter with a size rule), then prune."""

        schedule = self.schedule
        assert schedule is not None and self.period is not None and self.rollover_at is not None

        label = schedule.label(self.period)
        target = f"{self.baseFilename}.{label}"

        if self.size is not None or os.path.exists(self.rotation_filename(target)):
            counter = 1

            while os.path.exists(self.rotation_filename(f"{target}.{counter}")):
                counter += 1

            target = f"{target}.{counter}"

        self.rotate(self.baseFilename, self.rotation_filename(target))

        if self.period_ended():  # Not just a size rollover within the period
            self.start_next_period()

        self.prune_labeled()

    def period_ended(self) -> bool:
        """True when the schedule's current period is over. Always false without a schedule."""

        return self.rollover_at is not None and time.time() >= self.rollover_at

    def start_next_period(self) -> None:
        """Make the period that contains now the current one, and schedule its end."""

        schedule = self.schedule
        assert schedule is not None

        now = schedule.now()
        self.period = schedule.period_start(now)
        self.rollover_at = schedule.to_timestamp(schedule.next_boundary(now))

    def is_empty(self) -> bool:
        """True when nothing has been written to the current file."""

        stream = self.stream

        if stream is None:
            return not os.path.exists(self.baseFilename) or os.path.getsize(self.baseFilename) == 0

        stream.seek(0, 2)

        return stream.tell() == 0

    def prune_labeled(self) -> None:
        """Keep the newest *backup_count* labeled backups; delete the rest."""

        folder, base = os.path.split(self.baseFilename)
        backups: list[tuple[tuple[str, int], str]] = []

        for name in os.listdir(folder or "."):
            if name.startswith(base + "."):
                key = backup_sort_key(name[len(base) + 1:])

                if key is not None:
                    backups.append((key, os.path.join(folder, name)))

        backups.sort()

        for _, path in backups[:max(0, len(backups) - self.backup_count)]:
            os.remove(path)


#####################
# Shared file table #
#####################

@dataclass
class SharedFile:
    """One open log file: its handler, the setup it was opened with, its settings, and who uses it."""

    handler: logging.FileHandler
    kind: str
    settings: dict[str, object]
    owners: Counter[str] = field(default_factory=Counter)


SHARED_FILES: dict[str, SharedFile] = {}  # Every open log file in the process, keyed by file_key()
LAB_HANDLERS: "weakref.WeakSet[logging.Handler]" = weakref.WeakSet()  # Handlers logger-lab made, which it alone closes
SHARED_FILES_LOCK = threading.RLock()  # Guards SHARED_FILES and every handler swap (each check-then-change)


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

    The file output calls this instead of constructing a handler, so a file is never
    opened twice. When *path* is already open:

    * same *kind*, same *settings* → the existing handler is shared;
    * same *kind*, different *settings* → shared with the **first** settings, and a
      `SharedFileSettingsWarning` names what was ignored;
    * different *kind* → `LogFileClashError`, because one handler can't be both.

    Exception: if the only logger using *path* is the one asking, it is being rebuilt,
    so a new handler with the new kind/settings replaces the old one.

    Args:
        path:         The log file.
        kind:         The setup that must match to share, e.g. ``"FILE[TEXT]+ROTATING"``.
        settings:     The handler settings that must agree to share (encoding, sizes).
        open_handler: Builds the handler when the file isn't open yet.
        logger_name:  The logger asking, for ownership and messages.
    Returns:
        The handler for *path*, newly opened or shared.
    Raises:
        `LogFileClashError`: If another logger has *path* open with a different setup.
    Example::
        handler = share_file_handler(
            log_path, kind="FILE[TEXT]", settings={"encoding": "utf-8"},
            open_handler=lambda: LabFileHandler(log_path, encoding="utf-8", backup_count=3),
            logger_name=__name__,
        )
    """

    owner = logger_name or UNNAMED
    key = file_key(path)

    with SHARED_FILES_LOCK:
        shared = SHARED_FILES.get(key)

        # Closed outside the table (e.g. handler.close() by hand), so treat it as gone. Don't test
        # `stream is None`: a rotating handler sets that briefly mid-rollover, and a second handler would open.
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


###########################################
# Putting handlers on and taking them off #
###########################################

def release_handler(handler: logging.Handler, logger_name: str | None = None) -> None:
    """
    Release *logger_name*'s use of *handler*, closing it once nobody uses it.

    A shared file handler stays open while any other logger still writes to it.
    Other handlers logger-lab created are closed straight away. Handlers logger-lab
    did *not* create are left open, because they may serve other loggers we know nothing about.

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


def install_handlers(
    logger: logging.Logger,
    factories: Iterable[Callable[[], list[logging.Handler]]],
    dispatcher: Callable[..., list[logging.Handler]] | None = None,
) -> None:
    """
    Build every handler from *factories*, then put them on *logger* in one atomic swap.

    1. Each factory runs. If one raises, the handlers built so far are released and
       *logger* is left exactly as it was.
    2. If a *dispatcher* is given (the catalysts, such as ``ASYNC``), it is called with
       ``handlers=`` the built outputs. It returns what goes on the logger instead, and
       it owns the outputs from then on.
    3. ``logger.handlers`` is replaced in a single assignment. A thread logging at that
       moment finishes its record on the old list. It never sees a half-built one.
    4. The old handlers are released (`release_handler`).

    Args:
        logger:     The logger to (re)configure.
        factories:  Zero-argument callables, each returning output handlers.
        dispatcher: Optional callable taking ``handlers=`` and returning the logger's handlers.
    Example::
        install_handlers(logger, [lambda: [logging.StreamHandler()]])
    """

    new_handlers: list[logging.Handler] = []

    try:
        for factory in factories:
            new_handlers += factory()

        if dispatcher is not None:
            new_handlers = dispatcher(handlers=new_handlers)

    except BaseException:
        for handler in new_handlers:
            release_handler(handler, logger.name)

        raise

    with SHARED_FILES_LOCK:  # concurrent installations on one logger must not both release the same old list
        old_handlers = logger.handlers
        logger.handlers = new_handlers

    for handler in old_handlers:
        release_handler(handler, logger.name)


def clear_handlers(logger: logging.Logger) -> None:
    """
    Detach and release every handler on *logger* in one atomic swap.

    Releasing matters for file handlers. A detached but open handler keeps its
    file locked (on Windows, that blocks rotation) and leaks the descriptor.
    A shared file handler stays open while another logger still uses it, and
    handlers logger-lab didn't create are detached but never closed.
    It is idempotent, so it is safe to call on a fresh logger.

    Args:
        logger: The logger whose handlers will be removed and released.
    """

    install_handlers(logger, [])


#############################
# Configuring a new handler #
#############################

def configure_handler(handler: HandlerT, level: int, formatter: logging.Formatter | None = None) -> HandlerT:
    """
    Apply *level* and *formatter* to *handler* and return it.

    This is the **shared handler skeleton**. Every output calls it for each
    handler it creates, so the configuration contract is enforced in one place:

    1. Set the logging level on the handler.
    2. Attach the formatter (if supplied; Rich handlers manage their own).
    3. Record it as logger-lab's own, so `release_handler` may close it later.

    Args:
        handler:   Any `logging.Handler` subclass.
        level:     A standard `logging` level constant.
        formatter: Pre-built formatter to attach, or ``None`` for handlers
                   that manage their own formatting (e.g. ``RichHandler``).

    Returns:
        The same *handler* instance, changed in place, for one-line use inside
        an output's ``build``::

            return [configure_handler(RichHandler(), level)]
    """

    handler.setLevel(level)

    if formatter is not None:
        handler.setFormatter(formatter)

    with SHARED_FILES_LOCK:
        LAB_HANDLERS.add(handler)

    return handler


#################
# Log directory #
#################

def get_log_dir(path: Path | str = DEFAULT_LOG_DIR) -> Path:
    """
    Ensure the log directory exists and return it as a `pathlib.Path`.

    Creates the directory (and any missing parents) if it does not exist.
    This is the **single place** where the file output creates the
    log directory. Nothing else should call `os.makedirs` or
    `pathlib.Path.mkdir` directly.

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
