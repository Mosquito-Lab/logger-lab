"""
Exception hierarchy for logger-lab.

All exceptions inherit from `LabError`. Consumers can write one broad
``except LabError`` or catch specific subclasses.

Hierarchy
---------
::

    LabError
    ├── LabRegistryError
    │   ├── InvalidNameError             not a member or value of that kind's enum
    │   ├── TheoryNotFoundError          valid TheoryType with no registered spec (placeholder)
    │   └── RegistrationError            a spec that can't be registered
    ├── LabConfigurationError
    │   ├── InvalidLevelError            level is not a known name or an integer 0 or above
    │   ├── CompositionError             a composition that can't work (the message says how to fix it)
    │   ├── HandlerConfigurationError    handler failed to initialize
    │   │   └── LogDirectoryError        filesystem mkdir/access failure
    │   └── LogFileClashError            a file is already open with a different setup
    └── BuilderError                     nothing queued, or ASYNC with nothing built to wrap

    ProfileSuggestionWarning   (UserWarning)  a hand-made composition that a profile already provides
    SharedFileSettingsWarning  (UserWarning)  a shared file keeps its first settings

Design notes
------------
* Every error builds its own message from the arguments it takes. Callers
  never format strings themselves.
* Messages have no final period, like the stdlib's exceptions.
* ``HandlerConfigurationError`` and its subclass are raised with ``from err``,
  which keeps the original traceback.
* ``InvalidLevelError`` is raised by ``normalize_level_name`` for any unknown
  level name or invalid number. There is no silent fallback.
"""

from collections.abc import Iterable


########
# Root #
########

class LabError(Exception):
    """
    Base class for all logger-lab exceptions.

    Catch it to handle any error the library can raise.

    Example::
        try:
            logger = lab().with_profile("typo").build(__name__)
        except LabError as exc:
            print(f"logger-lab error: {exc}")
    """


###################
# Registry errors #
###################

class LabRegistryError(LabError):
    """Base class for name-resolution and registration failures."""


class InvalidNameError(LabRegistryError):
    """
    Raised when a name is neither a member nor a value of its kind's enum.

    Args:
        kind:  What was being named: ``"output"``, ``"feature"``, ``"format"``,
               ``"catalyst"``, ``"profile"`` or ``"theory"``. Kept as ``.kind``.
        name:  The unrecognized name that was provided.
        valid: The valid value strings, listed in the message.
    Example::
        raise InvalidNameError("output", "screen", ["CONSOLE", "FILE", "RELAY"])
        # InvalidNameError: 'screen' is not a recognized output name. Valid names: CONSOLE, FILE, RELAY
    """

    def __init__(self, kind: str, name: object, valid: Iterable[str]) -> None:
        self.kind = kind
        super().__init__(
            f"'{name}' is not a recognized {kind} name. "
            f"Valid names: {', '.join(valid)}"
        )


class TheoryNotFoundError(LabRegistryError):
    """
    Raised when a valid `TheoryType` has no registered spec yet.

    Every theory starts as a placeholder. Its enum value exists so the idea
    has a name, but nothing is registered until the theory actually works.

    Args:
        theory: The `TheoryType` value that was looked up.
    Example::
        raise TheoryNotFoundError(TheoryType.TRACE)
        # TheoryNotFoundError: theory 'TRACE' is still a placeholder. No spec is registered for it yet
    """

    def __init__(self, theory: object) -> None:
        name = getattr(theory, "value", str(theory))
        super().__init__(f"theory '{name}' is still a placeholder. No spec is registered for it yet")


class RegistrationError(LabRegistryError):
    """
    Raised when a theory can't be registered, or a lookup finds nothing registered.

    `register_theory` raises it for a bad spec: the wrong spec type, a member that isn't a
    `TheoryType`, a ``build`` that isn't callable, or a spec that fits no output. The lookups
    raise it for a member with no spec or profile recipe.

    Args:
        member: The enum member being registered.
        reason: What is wrong with it.
    Example::
        raise RegistrationError(Output.FILE, "build is not callable")
        # RegistrationError: cannot register 'FILE': build is not callable
    """

    def __init__(self, member: object, reason: str) -> None:
        key = getattr(member, "value", str(member))
        super().__init__(f"cannot register '{key}': {reason}")


########################
# Configuration errors #
########################

class LabConfigurationError(LabError):
    """Base class for errors caused by incorrect configuration."""


class InvalidLevelError(LabConfigurationError):
    """
    Raised when a level is neither a known level name nor an integer ``0`` or above.

    `normalize_level_name` raises it, and so do `with_level()` and
    `with_subscriber(level=...)`, which call it. The message lists the standard
    names. Custom names added with `logging.addLevelName` are accepted too.

    Args:
        level: The invalid level value that was provided.
    Example::
        raise InvalidLevelError("LOUD")
        # InvalidLevelError: 'LOUD' is not a valid logging level.
        # Valid names: DEBUG, INFO, WARNING, ERROR, CRITICAL (or an integer 0 or above)
    """

    VALID = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")  # The standard names the message lists

    def __init__(self, level: object) -> None:
        super().__init__(
            f"'{level}' is not a valid logging level. "
            f"Valid names: {', '.join(self.VALID)} (or an integer 0 or above)"
        )


class CompositionError(LabConfigurationError):
    """
    Raised by `LabBuilder.plan()` when a composition can't work. The message says how to fix it.

    Some examples:

    * a feature with no output it fits;
    * ``on=`` naming an output that isn't queued;
    * two detail features, or two formats, on one output;
    * a detail feature on a JSON output;
    * an unknown option, or a second profile.

    Args:
        message: What is wrong and how to fix it.
    Example::
        raise CompositionError("'ROTATING' needs a file output: add .with_output('file'), "
                               "or start from a profile such as 'investigator'")
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)


class HandlerConfigurationError(LabConfigurationError):
    """
    Raised when a logging handler fails to initialize.

    Always raise it with ``from err``, so the original traceback is not lost.

    Args:
        handler_type: Name or type of the handler that failed.
        reason:       Human-readable description of the failure.
    Example::
        raise HandlerConfigurationError(RichHandler, "no console available") from err
        # HandlerConfigurationError: failed to configure RichHandler: no console available
    """

    def __init__(self, handler_type: object, reason: str) -> None:
        name = getattr(handler_type, "__name__", str(handler_type))
        super().__init__(f"failed to configure {name}: {reason}")


class LogDirectoryError(HandlerConfigurationError):
    """
    Raised when the log directory cannot be created or accessed.

    Args:
        path:   The directory path that could not be created or accessed.
        reason: Human-readable description of the failure.
    Example::
        raise LogDirectoryError("/var/log/locked", "permission denied") from err
        # LogDirectoryError: failed to configure LabFileHandler:
        #   cannot create or access log directory '/var/log/locked': permission denied
    """

    def __init__(self, path: object, reason: str) -> None:
        # Only the file output creates directories, so its handler is the one that failed.
        super().__init__(
            "LabFileHandler",
            f"cannot create or access log directory '{path}': {reason}",
        )


class LogFileClashError(LabConfigurationError):
    """
    Raised when a logger asks for a file that another logger has open with a different setup.

    Every log file has exactly one handler in the process. Every logger that
    writes to the file shares it. So they must all use the same format and file
    features. One handler can't be both plain and rotating, or both text and JSON.

    Args:
        path:      The log file (its table key).
        held_by:   Loggers already writing to it.
        held_as:   The setup it is open with, e.g. ``"FILE[TEXT]"``.
        wanted_by: The logger asking.
        wanted_as: The setup it asked for, e.g. ``"FILE[TEXT]+ROTATING"``.
    Example::
        raise LogFileClashError("/app/logs/app.log", held_by=["app.loaders"], held_as="FILE[TEXT]",
                                wanted_by="app.bots", wanted_as="FILE[TEXT]+ROTATING")
        # LogFileClashError: logger 'app.bots' asked for '/app/logs/app.log' as FILE[TEXT]+ROTATING,
        # but it is already open as FILE[TEXT] for 'app.loaders'. …
    """

    def __init__(self, path: object, *, held_by: list[str], held_as: str, wanted_by: str, wanted_as: str) -> None:
        holders = ", ".join(f"'{name}'" for name in held_by)
        super().__init__(
            f"logger '{wanted_by}' asked for '{path}' as {wanted_as}, but it is already open as "
            f"{held_as} for {holders}. A log file has one handler, shared by every logger that writes "
            f"to it, so they must all use the same format and file features. To keep both setups, "
            f"give one its own file with with_output('file', filename=...)"
        )


##################
# Builder errors #
##################

class BuilderError(LabError):
    """
    Raised when there is nothing to build.

    `LabBuilder.plan()` raises it when nothing is queued. The ``ASYNC``
    catalyst raises it when the outputs built no handlers for it to wrap, such
    as a relay output with no subscribers.

    Args:
        message: What is missing and how to fix it.
    Example::
        raise BuilderError("nothing is queued: add a profile (.with_profile()) or an output (.with_output())")
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)


############
# Warnings #
############

class ProfileSuggestionWarning(UserWarning):
    """
    Warned when a composition queued by hand is one that a profile already provides.

    It is not an error, because the composition works. It points at the
    simpler way to say the same thing: start from the profile, then add
    features.

    Args:
        profile:     The matching profile's value, e.g. ``"INVESTIGATOR"``.
        composition: What the profile composes, e.g. ``"console + file"``.
    Example::
        lab().with_output("console").with_output("file").build(__name__)
        # ProfileSuggestionWarning: console + file is the 'INVESTIGATOR' profile: use
        # .with_profile('investigator'), then add features or options on top
    """

    def __init__(self, profile: str, composition: str) -> None:
        super().__init__(
            f"{composition} is the '{profile}' profile: use .with_profile('{profile.lower()}'), "
            f"then add features or options on top"
        )


class SharedFileSettingsWarning(UserWarning):
    """
    Warned when a logger joins a shared log file with different settings.

    The file's handler is already open, so it keeps the settings it was opened
    with. Those are the first logger's settings.

    Args:
        path:    The log file (its table key).
        kept:    The settings the shared handler keeps.
        ignored: The settings the joining logger asked for.
        owner:   The joining logger.
    Example::
        lab().with_output("file").with_feature("ROTATING", max_bytes=5_242_880).build("app.loaders")
        lab().with_output("file").with_feature("ROTATING", max_bytes=1_048_576).build("app.bots")
        # SharedFileSettingsWarning: logger 'app.bots' joined '/app/logs/app.log', which keeps
        # its first settings (max_bytes=5242880); ignoring max_bytes=1048576
    """

    def __init__(self, path: object, *, kept: dict[str, object], ignored: dict[str, object], owner: str) -> None:
        differs = [key for key in ignored if kept.get(key) != ignored[key]]
        kept_text = ", ".join(f"{key}={kept.get(key)!r}" for key in differs)
        ignored_text = ", ".join(f"{key}={ignored[key]!r}" for key in differs)
        super().__init__(
            f"logger '{owner}' joined '{path}', which keeps its first settings ({kept_text}); "
            f"ignoring {ignored_text}"
        )
