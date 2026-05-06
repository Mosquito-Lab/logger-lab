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
    │   ├── ExperimentNotFoundError    valid ExperimentType not in EXPERIMENTS dict
    │   ├── ProfileNotFoundError       valid ProfileType not in PROFILES dict
    │   ├── InvalidExperimentName      string cannot coerce to ExperimentType
    │   └── InvalidProfileName         string cannot coerce to ProfileType
    ├── LabConfigurationError
    │   ├── InvalidLevelError          level is not a valid string or int
    │   ├── HandlerConfigurationError  handler failed to initialise
    │   │   └── LogDirectoryError      filesystem mkdir/access failure
    │   ├── ExperimentRegistrationError  callable doesn't satisfy ExperimentFactory
    │   └── ProfileRegistrationError     callable doesn't satisfy ProfileFactory
    └── BuilderError                   build() called with nothing queued

Design notes
------------
* Every leaf class accepts the minimum arguments needed to produce a
  self-describing message so callers never have to format strings
  themselves.
* ``HandlerConfigurationError`` and its subclass accept an optional
  ``cause`` that is chained via ``raise ... from cause`` at the
  raise-site, preserving the original traceback.
* ``InvalidLevelError`` exists for callers who want to enforce strictness
  but ``normalise_level_name`` keeps its INFO fallback — raise the class
  yourself when you need strict behaviour.
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
    unrecognised or because the resolved enum key has no entry in the
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


class InvalidExperimentName(LabRegistryError):
    """Raised when a string cannot be coerced to any
    :class:`~logger_lab.core.enums.ExperimentType` value.

    This fires in :func:`~logger_lab.logging_kernel.handlers.normalise_exp_name`
    before a registry lookup is even attempted.

    Args:
        name: The unrecognised string that was provided.

    Example::

        raise InvalidExperimentName("typo")
        # InvalidExperimentName: 'typo' is not a recognised experiment name.
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
        name: The unrecognised string that was provided.

    Example::

        raise InvalidProfileName("ghost")
        # InvalidProfileName: 'ghost' is not a recognised profile name.
        # Valid names: observer, investigator, conspiracy_theorist, ai_agent
    """

    def __init__(self, name: str) -> None:
        from logger_lab.core.enums import ProfileType

        valid = ", ".join(p.value for p in ProfileType)
        super().__init__(
            f"'{name}' is not a recognised profile name. "
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
    """Raised when a level value is neither a recognised string name nor
    a valid :mod:`logging` integer constant.

    :func:`~logger_lab.logging_kernel.handlers.normalise_level_name`
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
    """Raised when a logging handler fails to initialise.

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
            f"Add at least one via .with_experiment() or .with_profile()."
        )
