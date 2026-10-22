"""
Exception hierarchy for logger-lab.

All exceptions inherit from :class:`LabError` so library consumers can
write a single broad ``except LabError`` or catch specific subclasses
for fine-grained handling.

Hierarchy
---------
::

    LabError
    ├── LabRegistryError
    │   ├── ExperimentNotFoundError      valid ExperimentType not in EXPERIMENTS dict
    │   ├── ProfileNotFoundError         valid ProfileType not in PROFILES dict
    │   ├── TheoryNotFoundError          valid TheoryType with no registered factory (placeholder)
    │   ├── InvalidExperimentName        string cannot coerce to ExperimentType
    │   ├── InvalidProfileName           string cannot coerce to ProfileType
    │   └── InvalidTheoryName            string cannot coerce to TheoryType
    ├── LabConfigurationError
    │   ├── InvalidLevelError            level is not a valid string or int
    │   ├── HandlerConfigurationError    handler failed to initialize
    │   │   └── LogDirectoryError        filesystem mkdir/access failure
    │   ├── ExperimentClashError         two experiments claim the same channel
    │   ├── LogFileClashError            a file is already open with a different experiment
    │   ├── ExperimentRegistrationError  callable doesn't satisfy ExperimentFactory
    │   └── ProfileRegistrationError     callable doesn't satisfy ProfileFactory
    └── BuilderError                     build() called with nothing queued

    DuplicateExperimentWarning (UserWarning)  same experiment queued twice; first kept
    SharedFileSettingsWarning  (UserWarning)  shared file keeps its first settings

Design notes
------------
* Every leaf class accepts the minimum arguments needed to produce a
  self-describing message so callers never have to format strings
  themselves.
* ``HandlerConfigurationError`` and its subclass accept an optional
  ``cause`` that is chained via ``raise ... from cause`` at the
  raise-site, preserving the original traceback.
* ``InvalidLevelError`` exists for callers who want to enforce strictness
  but ``normalize_level_name`` keeps its INFO fallback — raise the class
  yourself when you need strict behavior.
"""

########
# Root #
########

class LabError(Exception):
    """Base class for all logger-lab exceptions.

    Catch this to handle any error the library can raise::

        try:
            logger = get_logger(__name__, profile="typo")
        except LabError as exc:
            print(f"logger-lab error: {exc}")
    """


###################
# Registry errors #
###################

class LabRegistryError(LabError):
    """Base class for registry lookup and name-resolution failures.

    Raised (or subclassed) whenever a name cannot be resolved to a
    registered experiment or profile, either because the string is
    unrecognized or because the resolved enum key has no entry in the
    registry dict.
    """


class ExperimentNotFoundError(LabRegistryError):
    """Raised when a valid :class:`~logger_lab.core.enums.ExperimentType`
    has no corresponding entry in the ``EXPERIMENTS`` registry.

    This means the enum value exists but no factory callable was
    registered for it — typically a missing entry in ``registry.py``.

    Args:
        experiment: The ``ExperimentType`` value that was looked up.

    Example::
        raise ExperimentNotFoundError(ExperimentType.AI)
        # ExperimentNotFoundError: experiment 'ai' is a valid ExperimentType
        # but is not registered in EXPERIMENTS
    """

    def __init__(self, experiment: object) -> None:
        name = getattr(experiment, "value", str(experiment))
        super().__init__(
            f"experiment '{name}' is a valid ExperimentType "
            f"but is not registered in EXPERIMENTS"
        )


class ProfileNotFoundError(LabRegistryError):
    """Raised when a valid :class:`~logger_lab.core.enums.ProfileType`
    has no corresponding entry in the ``PROFILES`` registry.

    Args:
        profile: The ``ProfileType`` value that was looked up.

    Example::

        raise ProfileNotFoundError(ProfileType.OBSERVER)
        # ProfileNotFoundError: profile 'observer' is a valid ProfileType
        # but is not registered in PROFILES
    """

    def __init__(self, profile: object) -> None:
        name = getattr(profile, "value", str(profile))
        super().__init__(
            f"profile '{name}' is a valid ProfileType "
            f"but is not registered in PROFILES"
        )


class TheoryNotFoundError(LabRegistryError):
    """Raised when a valid `TheoryType` has no registered factory.

    Every theory starts as a placeholder: the enum value exists so the idea
    has a name, but nothing is registered until the theory actually works.

    Args:
        theory: The ``TheoryType`` value that was looked up.
    Example::
        raise TheoryNotFoundError(TheoryType.ASYNC)
        # TheoryNotFoundError: theory 'ASYNC' is still a placeholder — no factory
        # is registered in THEORIES yet
    """

    def __init__(self, theory: object) -> None:
        name = getattr(theory, "value", str(theory))
        super().__init__(
            f"theory '{name}' is still a placeholder — no factory is registered in THEORIES yet"
        )


class InvalidExperimentName(LabRegistryError):
    """Raised when a string cannot be coerced to any
    :class:`~logger_lab.core.enums.ExperimentType` value.

    This fires in :func:`~logger_lab.logging_kernel.handlers.normalize_exp_name`
    before a registry lookup is even attempted.

    Args:
        name: The unrecognized string that was provided.

    Example::

        raise InvalidExperimentName("typo")
        # InvalidExperimentName: 'typo' is not a recognized experiment name.
        # Valid names: standard, verbose, minimalist, file, rotating_file, AI
    """

    def __init__(self, name: str) -> None:
        # Lazily imported to avoid circular dependency at module load time.
        from logger_lab.core.enums import ExperimentType

        valid = ", ".join(e.value for e in ExperimentType)
        super().__init__(
            f"'{name}' is not a recognised experiment name. "
            f"Valid names: {valid}"
        )


class InvalidProfileName(LabRegistryError):
    """Raised when a string cannot be coerced to any
    :class:`~logger_lab.core.enums.ProfileType` value.

    Args:
        name: The unrecognized string that was provided.

    Example::

        raise InvalidProfileName("ghost")
        # InvalidProfileName: 'ghost' is not a recognized profile name.
        # Valid names: observer, investigator, conspiracy_theorist, ai_agent
    """

    def __init__(self, name: str) -> None:
        from logger_lab.core.enums import ProfileType

        valid = ", ".join(p.value for p in ProfileType)
        super().__init__(
            f"'{name}' is not a recognised profile name. "
            f"Valid names: {valid}"
        )


class InvalidTheoryName(LabRegistryError):
    """Raised when a string cannot be coerced to any `TheoryType` value.

    Args:
        name: The unrecognized string that was provided.
    Example::
        raise InvalidTheoryName("ghost")
        # InvalidTheoryName: 'ghost' is not a recognised theory name.
        # Valid names: ASYNC, DB, HTTP, PERFORMANCE, SEC, TIMED_FILE, TRACE
    """

    def __init__(self, name: object) -> None:
        from logger_lab.core.enums import TheoryType

        valid = ", ".join(t.value for t in TheoryType)
        super().__init__(
            f"'{name}' is not a recognised theory name. "
            f"Valid names: {valid}"
        )


########################
# Configuration errors #
########################

class LabConfigurationError(LabError):
    """Base class for errors caused by incorrect configuration.

    Raised when valid-looking inputs produce an invalid setup — a
    misconfigured handler, a bad level value, or a callable that does
    not satisfy the required protocol.
    """


class InvalidLevelError(LabConfigurationError):
    """Raised when a level value is neither a recognized string name nor
    a valid :mod:`logging` integer constant.

    :func:`~logger_lab.logging_kernel.handlers.normalize_level_name`
    keeps its ``INFO`` fallback for unknown strings; raise this class
    explicitly when strict level validation is required.

    Args:
        level: The invalid level value that was provided.

    Example::

        raise InvalidLevelError("LOUD")
        # InvalidLevelError: 'LOUD' is not a valid logging level.
        # Valid names: DEBUG, INFO, WARNING, ERROR, CRITICAL
    """

    _VALID = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")

    def __init__(self, level: object) -> None:
        super().__init__(
            f"'{level}' is not a valid logging level. "
            f"Valid names: {', '.join(self._VALID)}"
        )


class HandlerConfigurationError(LabConfigurationError):
    """Raised when a logging handler fails to initialize.

    Wraps lower-level exceptions (e.g. :exc:`OSError`,
    :exc:`PermissionError`) so the caller receives a lab-domain error
    with a meaningful message while the original cause is preserved via
    ``__cause__``.

    Always raise with ``from err`` so the original traceback is not lost::

        try:
            handler = FileHandler(path)
        except OSError as err:
            raise HandlerConfigurationError("FileHandler", str(err)) from err

    Args:
        handler_type: Name or type of the handler that failed.
        reason:       Human-readable description of the failure.
    """

    def __init__(self, handler_type: object, reason: str) -> None:
        name = getattr(handler_type, "__name__", str(handler_type))
        super().__init__(f"failed to configure {name}: {reason}")


class LogDirectoryError(HandlerConfigurationError):
    """Raised when the log directory cannot be created or accessed.

    Subclass of :class:`HandlerConfigurationError` so it can be caught
    by handlers that deal with any filesystem-related setup failure, or
    caught specifically when only directory access matters.

    Always raise with ``from err``::

        try:
            path.mkdir(parents=True, exist_ok=True)
        except OSError as err:
            raise LogDirectoryError(path, str(err)) from err

    Args:
        path:   The directory path that could not be created or accessed.
        reason: Human-readable description of the failure.

    Example::

        raise LogDirectoryError("/var/log/locked", "permission denied") from err
        # LogDirectoryError: failed to configure FileHandler:
        #   cannot create or access log directory '/var/log/locked': permission denied
    """

    def __init__(self, path: object, reason: str) -> None:
        # Directory errors only arise from file-based handlers so
        # "FileHandler" is always the correct handler_type here.
        super().__init__(
            "FileHandler",
            f"cannot create or access log directory '{path}': {reason}",
        )


class ExperimentClashError(LabConfigurationError):
    """Raised when two different experiments would write to the same channel.

    A logger holds at most one experiment per channel — one console, one
    file, one JSON — so handlers never compete for the same output (two
    consoles printing every record twice, two handlers fighting over one
    file).  Pick the one you want and drop the other.

    Args:
        channel: The `Channel` both experiments claim.
        first:   Description of the experiment that claimed it first.
        second:  Description of the experiment that clashed with it.
    Example::
        raise ExperimentClashError(Channel.CONSOLE, "'STANDARD' (from profile 'INVESTIGATOR')",
                                   "'MINIMALIST' (queued)")
        # ExperimentClashError: 'MINIMALIST' (queued) clashes with 'STANDARD' (from
        # profile 'INVESTIGATOR'): both write to the CONSOLE channel. …
    """

    def __init__(self, channel: object, first: str, second: str) -> None:
        name = getattr(channel, "value", str(channel))
        super().__init__(
            f"{second} clashes with {first}: both write to the {name} channel. "
            f"A logger takes at most one experiment per channel (CONSOLE, FILE, JSON) "
            f"so no two handlers compete for the same output — keep one of them."
        )


class LogFileClashError(LabConfigurationError):
    """Raised when a logger asks for a file another logger already has open with a different experiment.

    Every log file has exactly one handler in the process, shared by every
    logger writing to it — so they must all use the same file experiment
    (one handler can't be both a plain and a rotating file).

    Args:
        path:      The log file (its table key).
        held_by:   Loggers already writing to it.
        held_as:   The experiment it is open as, e.g. ``"FILE"``.
        wanted_by: The logger asking.
        wanted_as: The experiment it asked for, e.g. ``"ROTATING"``.
    Example::
        raise LogFileClashError("/app/logs/app.log", held_by=["app.loaders"], held_as="FILE",
                                wanted_by="app.bots", wanted_as="ROTATING")
        # LogFileClashError: logger 'app.bots' asked for '/app/logs/app.log' as ROTATING, but it
        # is already open as FILE for 'app.loaders'. …
    """

    def __init__(self, path: object, *, held_by: list[str], held_as: str, wanted_by: str, wanted_as: str) -> None:
        holders = ", ".join(f"'{name}'" for name in held_by)
        super().__init__(
            f"logger '{wanted_by}' asked for '{path}' as {wanted_as}, but it is already open as "
            f"{held_as} for {holders}. A log file has one handler shared by every logger writing to it, "
            f"so they must use the same file experiment — or give one its own file with "
            f"with_file_args(filename=...)."
        )


class ExperimentRegistrationError(LabConfigurationError):
    """Raised when a callable registered in ``EXPERIMENTS`` does not
    satisfy the :class:`~logger_lab.core.registry.ExperimentFactory`
    protocol.

    Validation fires at registration time (when the ``EXPERIMENTS`` dict
    is populated) so bad entries are caught before any logger is built.

    Args:
        name:   The :class:`~logger_lab.core.enums.ExperimentType` key
                that was being registered.
        reason: Description of what the callable got wrong.

    Example::

        raise ExperimentRegistrationError(ExperimentType.AI, "not callable")
        # ExperimentRegistrationError: cannot register experiment 'ai': not callable
    """

    def __init__(self, name: object, reason: str) -> None:
        key = getattr(name, "value", str(name))
        super().__init__(f"cannot register experiment '{key}': {reason}")


class ProfileRegistrationError(LabConfigurationError):
    """Raised when a callable registered in ``PROFILES`` does not satisfy
    the :class:`~logger_lab.core.registry.ProfileFactory` protocol.

    Args:
        name:   The :class:`~logger_lab.core.enums.ProfileType` key
                that was being registered.
        reason: Description of what the callable got wrong.

    Example::

        raise ProfileRegistrationError(ProfileType.OBSERVER, "not callable")
        # ProfileRegistrationError: cannot register profile 'observer': not callable
    """

    def __init__(self, name: object, reason: str) -> None:
        key = getattr(name, "value", str(name))
        super().__init__(f"cannot register profile '{key}': {reason}")


##################
# Builder errors #
##################

class BuilderError(LabError):
    """Raised when :meth:`~logger_lab.core.builder.LabBuilder.build` is
    called in an invalid state.

    Currently, this means ``build()`` was called with neither a profile
    nor any experiments queued, which would produce a logger with zero
    handlers — almost certainly a misconfiguration rather than intentional.

    Args:
        name: The logger name passed to ``build()``.

    Example::

        raise BuilderError("my_app")
        # BuilderError: build('my_app') called with no experiments or profile
        # queued. Add at least one via .with_experiment() or .with_profile().
    """

    def __init__(self, name: str) -> None:
        super().__init__(
            f"build('{name}') called with no experiments or profile queued. "
            f"Add at least one via .with_experiment(), .with_profile() or .with_theory()."
        )


############
# Warnings #
############

class DuplicateExperimentWarning(UserWarning):
    """Warned when the same experiment is queued more than once.

    Not an error: asking for the same thing twice has one obvious meaning,
    so the builder keeps the first instance and skips the rest.  Usually
    a profile already includes the experiment you queued on top of it.

    Args:
        experiment: The duplicated experiment or theory.
        first:      Where it was queued first.
        again:      Where it was queued again.
    Example::
        lab().with_profile("investigator").with_experiment("FILE").build(__name__)
        # DuplicateExperimentWarning: 'FILE' is queued twice (from profile
        # 'INVESTIGATOR', then queued) — keeping the first and skipping the duplicate.
    """

    def __init__(self, experiment: object, first: str, again: str) -> None:
        name = getattr(experiment, "value", str(experiment))
        super().__init__(
            f"'{name}' is queued twice ({first}, then {again}) — "
            f"keeping the first and skipping the duplicate."
        )


class SharedFileSettingsWarning(UserWarning):
    """Warned when a logger joins a shared log file with different settings.

    The file's handler is already open, so it keeps the settings it was
    opened with — the first logger's.  Usually the fix is to set the file
    args once, the same everywhere, or give the logger its own filename.

    Args:
        path:    The log file (its table key).
        kept:    The settings the shared handler keeps.
        ignored: The settings the joining logger asked for.
        owner:   The joining logger.
    Example::
        # SharedFileSettingsWarning: logger 'app.bots' joined '/app/logs/app.log', which keeps
        # its first settings (max_bytes=5242880); ignoring max_bytes=1048576.
    """

    def __init__(self, path: object, *, kept: dict[str, object], ignored: dict[str, object], owner: str) -> None:
        differs = [key for key in ignored if kept.get(key) != ignored[key]]
        kept_text = ", ".join(f"{key}={kept.get(key)!r}" for key in differs)
        ignored_text = ", ".join(f"{key}={ignored[key]!r}" for key in differs)
        super().__init__(
            f"logger '{owner}' joined '{path}', which keeps its first settings ({kept_text}); "
            f"ignoring {ignored_text}."
        )
