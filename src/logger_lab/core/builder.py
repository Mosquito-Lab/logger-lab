"""
``LabBuilder`` — the fluent builder that composes profiles, experiments and theories
into one `logging.Logger`, and ``lab()``, its entry point.

The ``with_*`` methods only record what was asked for.  `plan()` turns that into the
ordered list of experiments to build — warning on duplicates and raising on channel
clashes — and `build()` builds exactly that list.
"""

import warnings
from functools import partial
from pathlib import Path
from logging import INFO, WARNING, Logger, getLogger

from logger_lab.logging_kernel.constants import DEFAULT_ENCODING, DEFAULT_FILENAME, DEFAULT_MAX_BYTES, \
    DEFAULT_BACKUP_COUNT, DEFAULT_LOG_DIR
from logger_lab.experiments.relay import Subscriber
from logger_lab.logging_kernel.dispatch import is_dispatcher
from logger_lab.logging_kernel.errors import BuilderError, DuplicateExperimentWarning, ExperimentClashError
from logger_lab.logging_kernel.handlers import install_handlers
from logger_lab.core.enums import ExperimentType, ProfileType, TheoryType
from logger_lab.core.registry import find_channel_clash, get_experiment, get_profile_experiments, get_theory
from logger_lab.logging_kernel.normalizers import (
    normalize_level_name, normalize_exp_name, normalize_profile_name, normalize_theory_name,
)


class LabBuilder:
    """
    Fluent builder for composing logger-lab configurations.

    Each ``with_*`` method mutates the builder and returns ``self`` so
    calls can be chained.  Call `build()` last to materialize the
    configured `logging.Logger`.

    At least one profile, experiment or theory must be queued before
    calling `build`; an empty builder raises `BuilderError`.

    Composition rules, enforced by `plan()`:
    * At most one experiment per channel — one console, one file, one JSON,
      one live relay, one dispatcher.  Two different experiments on one
      channel raise `ExperimentClashError`.
    * The same experiment queued twice warns (`DuplicateExperimentWarning`)
      and only the first instance is built.
    * Subscribers (`with_subscriber`) bring the ``relay`` experiment with them.
    """

    def __init__(self) -> None:
        """Start empty: no profile, nothing queued, no level (see `default_level`), default file args."""

        self._experiments: list[ExperimentType | TheoryType] = []
        self._theory_options: dict[TheoryType, dict[str, object]] = {}
        self._profile: ProfileType | None = None
        self._level: int | None = None  # None until with_level(); build() then uses default_level()
        self._file_args: dict[str, object] = {}
        self._subscribers: list[tuple[Subscriber, int | None]] = []

    def with_experiment(self, experiment: ExperimentType | str) -> "LabBuilder":
        """
        Queue an experiment to be applied during `build()`.

        Accepts either an `ExperimentType` enum member or its value string,
        case-insensitive (e.g. ``"standard"``, ``"AI"``, ``"ROTATING"``).
        Experiments are applied in the order they are queued, after the
        profile's (if any).  Theories go through `with_theory()` instead.

        Args:
            experiment: Experiment identifier — enum member or value string.
        Returns:
            ``self``, for method chaining.
        Raises:
            `InvalidExperimentName`:
                If *experiment* does not match any `ExperimentType` value.
        Example::
            lab().with_experiment("standard").with_experiment(ExperimentType.AI)
        """

        self._experiments.append(normalize_exp_name(experiment))

        return self

    def with_theory(self, theory: TheoryType | str, **options: object) -> "LabBuilder":
        """
        Queue a theory — an experiment still being researched — to be applied during `build()`.

        Accepts a `TheoryType` member or its value string, case-insensitive
        (e.g. ``"TIMED_FILE"``).  Theories follow the same channel rules as
        experiments and are built in queue order alongside them.

        *options* are passed to this theory's factory only, on top of the
        file args — for settings no other experiment has (e.g. a timed
        rotation's ``when``/``interval``).  Queuing the same theory again
        replaces its options.

        Args:
            theory:    Theory identifier — enum member or value string.
            **options: Extra keyword arguments for this theory's factory.
        Returns:
            ``self``, for method chaining.
        Raises:
            `InvalidTheoryName`:
                If *theory* does not match any `TheoryType` value.
        Example::
            lab().with_experiment("standard").with_theory("TIMED_FILE", when="midnight").build(__name__)
        """

        theory_enum = normalize_theory_name(theory)
        self._experiments.append(theory_enum)
        self._theory_options[theory_enum] = options

        return self

    def with_profile(self, profile: ProfileType | str) -> "LabBuilder":
        """
        Use a named profile instead of (or alongside) individual experiments.

        A profile expands into its declared experiments, which come *before*
        anything queued via `with_experiment()`/`with_theory()`.  Only one
        profile may be set; calling this again replaces the previous value.

        Args:
            profile: Profile identifier — enum member or value string.
        Returns:
            ``self``, for method chaining.
        Raises:
            `InvalidProfileName`:
                If *profile* does not match any `ProfileType` value.
        Example::
            lab().with_profile("investigator").build(__name__)
        """

        self._profile = normalize_profile_name(profile)

        return self

    def with_level(self, level: int | str) -> "LabBuilder":
        """
        Set the logging level applied to the logger and all handlers.

        Accepts level names, case-insensitive (``"DEBUG"``, custom names too), and
        integers ``0`` or above.  If never called, `default_level` decides: ``INFO``,
        or ``WARNING`` when ``minimalist`` is in the logger (e.g. ``observer``).

        Args:
            level: Logging level — name or integer.
        Returns:
            ``self``, for method chaining.
        Raises:
            `InvalidLevelError`: For an unknown name or an invalid number.
        Example::
            lab().with_level("WARNING").build(__name__)
            lab().with_level(logging.DEBUG).build(__name__)
        """

        self._level = normalize_level_name(level)

        return self

    def with_file_args(
        self,
        log_dir: Path | str = DEFAULT_LOG_DIR,
        filename: str = DEFAULT_FILENAME,
        encoding: str = DEFAULT_ENCODING,
        max_bytes: int = DEFAULT_MAX_BYTES,
        backup_count: int = DEFAULT_BACKUP_COUNT
    ) -> "LabBuilder":
        """
        Set where and how file-based experiments write their logs.

        Forwarded to every experiment and theory built — the profile's
        included. Each takes the args it understands — ``file`` uses
        ``log_dir``/``filename``/``encoding``, ``rotating_file`` uses all
        five — and console experiments (``standard``, ``verbose``,
        ``minimalist``, ``ai``) absorb them through ``**kwargs`` and ignore them.

        Note: calling this again replaces every arg, not just the ones
        passed — omitted args go back to their defaults.

        If never called, each file-based experiment uses its own defaults
        (``logs/app.log``). The directory is created automatically,
        including parents, when a file handler is built.

        Args:
            log_dir:      Directory in which log files are created, absolute or relative.
            filename:     Name of the log file inside *log_dir*.
            encoding:     File encoding.
            max_bytes:    Size in bytes at which a rotating file rolls over.
            backup_count: Number of rotated files to keep.
        Returns:
            ``self``, for method chaining.
        Example::
            lab().with_profile("investigator").with_file_args("/var/log/myapp").build(__name__)
            lab().with_experiment("ROTATING").with_file_args(
                log_dir="./run_logs", filename="run.log", max_bytes=1_048_576, backup_count=5,
            ).build(__name__)
        """

        self._file_args = {
            "log_dir": log_dir,
            "filename": filename,
            "encoding": encoding,
            "max_bytes": max_bytes,
            "backup_count": backup_count,
        }

        return self

    def with_subscriber(self, callback: Subscriber, level: int | str | None = None) -> "LabBuilder":
        """
        Hand every record to *callback* as it is logged (the ``relay`` experiment).

        Queues ``relay`` automatically if nothing else did.  Each call adds a
        subscriber, with its own optional *level*; ``None`` lets the logger's level
        decide.  The callback gets the `logging.LogRecord` itself — treat it as
        read-only.  With ``async`` it runs on the dispatch worker thread, otherwise
        on the thread that logged; for Qt, pass a signal's ``emit``.

        Args:
            callback: Called with each record that passes *level*.
            level:    Minimum level for this subscriber — name or integer, or ``None``.
        Returns:
            ``self``, for method chaining.
        Example::
            lab().with_profile("gui").with_subscriber(relay.record_logged.emit).build("LabFrame.feedback")
            lab().with_experiment("standard").with_subscriber(alerts.append, level="ERROR").build(__name__)
        """

        self._subscribers.append((callback, None if level is None else normalize_level_name(level)))

        return self

    def plan(self) -> list[ExperimentType | TheoryType]:
        """
        Return the experiments and theories `build()` will build, in order.

        Expands the profile into its declared experiments, then appends
        everything queued.  Along the way:

        1. A repeat of an experiment already planned warns with
           `DuplicateExperimentWarning` and is skipped — the first wins.
        2. Two *different* experiments on the same channel raise
           `ExperimentClashError` naming both and where each came from.

        Subscribers bring ``relay`` with them if it isn't already planned.

        Safe to call on its own to check a composition without building
        anything — no handlers are created and no files are opened.

        Returns:
            The de-duplicated, clash-free build order.
        Raises:
            `BuilderError`:
                If nothing is queued.
            `ExperimentClashError`:
                If two experiments claim the same channel.
            `TheoryNotFoundError`:
                If a queued theory is still a placeholder.
        Example::
            lab().with_profile("investigator").with_experiment("AI").plan()
            # → [ExperimentType.STANDARD, ExperimentType.FILE, ExperimentType.AI]
        """

        queued: list[tuple[ExperimentType | TheoryType, str]] = []

        if self._profile is not None:
            origin = f"from profile '{self._profile.value}'"
            queued += [(exp, origin) for exp in get_profile_experiments(self._profile)]

        queued += [(entry, "queued") for entry in self._experiments]

        if self._subscribers and ExperimentType.RELAY not in {entry for entry, _ in queued}:
            queued.append((ExperimentType.RELAY, "added by with_subscriber()"))

        if not queued:
            raise BuilderError("<plan>")

        # Insertion-ordered: entry → where it first came from
        planned: dict[ExperimentType | TheoryType, str] = {}

        for entry, origin in queued:
            if entry in planned:
                warnings.warn(DuplicateExperimentWarning(entry, planned[entry], origin), stacklevel=3)
                continue

            planned[entry] = origin

        clash = find_channel_clash(planned)

        if clash is not None:
            first, second, channel = clash
            raise ExperimentClashError(
                channel,
                first=f"'{first.value}' ({planned[first]})",
                second=f"'{second.value}' ({planned[second]})",
            )

        return list(planned)

    def build(self, name: str) -> Logger:
        """
        Materialize the configured `logging.Logger`.

        Construction order:
        1. `plan()` the composition — raises before anything is touched, so a
           bad composition never wipes an existing logger.
        2. Build every planned output (level, file args, a theory's own options,
           subscribers, and the logger name for file sharing); a dispatcher
           (``async``) then wraps them.  Swap the result onto the logger in one
           step (`install_handlers`) — a thread logging meanwhile sees the old
           handlers or the new ones, never a mix.  The old handlers are released.
        3. Set the final level and disable propagation.

        Thread-safe: any number of threads may build loggers at once, including
        the same name.  A single `LabBuilder` instance is not meant to be shared
        between threads while it is being configured.

        Args:
            name: Logger name passed to `logging.getLogger`,
            typically ``__name__``.
        Returns:
            A fully configured `logging.Logger` with
            ``propagate = False``.
        Raises:
            `BuilderError`:
                If no profile, experiments or theories have been queued.
            `ExperimentClashError`:
                If two experiments claim the same channel.
            `LogFileClashError`:
                If another logger has this logger's file open as a different experiment.
            `ExperimentNotFoundError` / `ProfileNotFoundError` / `TheoryNotFoundError`:
                If something queued is not in the registry.
        Example::
            logger = lab().with_experiment("AI").with_level("INFO").build(__name__)
            logger = lab().with_profile("investigator").with_file_args("/var/log/myapp").build(__name__)
        """

        if self._profile is None and not self._experiments and not self._subscribers:
            raise BuilderError(name)

        plan = self.plan()
        level = self._level if self._level is not None else default_level(plan)
        logger = getLogger(name)

        # File args are empty unless with_file_args() was called, so factories keep their own defaults.
        # logger_name lets file experiments share one handler per file across loggers.
        shared_kwargs: dict[str, object] = {"logger_name": name}

        if self._subscribers:
            shared_kwargs["subscribers"] = tuple(self._subscribers)

        outputs = []
        dispatch = None

        for entry in plan:

            if isinstance(entry, TheoryType):
                factory = get_theory(entry)
                kwargs = {**self._file_args, **self._theory_options.get(entry, {})}

            else:
                factory = get_experiment(entry)
                kwargs = self._file_args

            call = partial(factory, level, **{**kwargs, **shared_kwargs})

            if is_dispatcher(factory):  # at most one: dispatchers share the DISPATCH channel
                dispatch = call
            else:
                outputs.append(call)

        install_handlers(logger, outputs, dispatcher=dispatch)
        logger.setLevel(level)
        logger.propagate = False

        return logger


def default_level(plan: list[ExperimentType | TheoryType]) -> int:
    """
    Return the level a logger gets when `with_level()` wasn't called.

    ``INFO``, except ``WARNING`` when *plan* includes ``minimalist`` — which exists to
    stay quiet until something matters (the ``observer`` profile is just ``minimalist``).

    Args:
        plan: The build order from `LabBuilder.plan()`.
    Returns:
        ``logging.WARNING`` or ``logging.INFO``.
    Example::
        default_level([ExperimentType.MINIMALIST, ExperimentType.FILE])  # → WARNING
    """

    return WARNING if ExperimentType.MINIMALIST in plan else INFO


def lab() -> LabBuilder:
    """
    Return a fresh `LabBuilder()` instance.

    This is the intended entry point for fluent logger construction::

        from logger_lab import lab

        logger = (
            lab()
            .with_experiment("standard")
            .with_level("DEBUG")
            .build(__name__)
        )

    Returns:
        A new, unconfigured :class:`LabBuilder`.
    """

    return LabBuilder()
