import logging

from pathlib import Path

from logger_lab.core.enums import ExperimentType, ProfileType
from logger_lab.logging_kernel.errors import InvalidExperimentName, InvalidProfileName, LogDirectoryError


# Handler guard
def clear_handlers(logger: logging.Logger) -> None:
    """Remove all handlers from *logger* to prevent duplicate log output.

    Call this at the start of every profile and experiment that attaches
    new handlers.  It is idempotent — safe to call on a fresh logger.

    Args:
        logger: The logger whose handler list will be cleared.
    """

    logger.handlers.clear()


# Experiment skeleton — shared handler configuration
def configure_handler(
        handler: logging.Handler,
        level: int,
        formatter: logging.Formatter | None = None,
    ) -> logging.Handler:
    """Apply *level* and *formatter* to *handler* and return it.

    This is the **shared experiment skeleton**.  Every experiment calls
    this for each handler it creates so the configuration contract is
    enforced in one place:

    1. Set the logging level on the handler.
    2. Attach the formatter (if supplied; Rich handlers manage their own).

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

    return handler


# logger.DEBUG or 1
def normalise_level_name(level: int | str) -> int:
    """
    Coerce a level value to a :mod:`logging` integer constant.

    Accepts both string names (``"DEBUG"``, case-insensitive) and integer
    constants (``logging.DEBUG``).  Unknown string names fall back to
    ``logging.INFO`` — use `InvalidLevelError` at the call-site when strict validation is required.

    Args:
        level: Logging level as a string name or integer constant.
    Returns:
        An integer logging level.
    Example::
        normalise_level_name("debug")          # → 10  (logging.DEBUG)
        normalise_level_name(logging.WARNING)  # → 30
        normalise_level_name("NONSENSE")       # → 20  (logging.INFO, soft fallback)
    """

    if isinstance(level, str):
        return getattr(logging, level.upper(), logging.INFO)

    return level


# 'standard' or ExperimentType.STANDARD
def normalise_exp_name(experiment: "ExperimentType | str") -> "ExperimentType":
    """
    Coerce *experiment* to an `ExperimentType` enum.

    Accepts either the enum member itself or the string ``.value`` of the
    enum (e.g. ``"standard"``, ``"AI"``). String matching is case-insensitive.

    Args:
        experiment: An `ExperimentType` enum member or its string value.
    Returns:
        The matching `ExperimentType` member.
    Raises:
        `InvalidExperimentName` error:
            If *experiment* is a string that does not match any
            ``ExperimentType`` value.
    Example::
        normalise_exp_name("standard")          # → ExperimentType.STANDARD
        normalise_exp_name(ExperimentType.AI)   # → ExperimentType.AI (pass-through)
        normalise_exp_name("ghost")             # → raises InvalidExperimentName
    """

    # Lazy loaded so no runtime funny business
    from logger_lab.core.enums import ExperimentType

    if isinstance(experiment, ExperimentType):
        return experiment

    try:
        return ExperimentType(experiment.lower())

    except ValueError:
        raise InvalidExperimentName(experiment)


# 'conspiracy_theorist' or ExperimentType.CONSPIRACY_THEORIST
def normalise_profile_name(profile: "ProfileType | str") -> "ProfileType":
    """
    Coerce *profile* to a `ProfileType` enum.

    Accepts either the enum member itself or the string ``.value`` of the
    enum (e.g. ``"investigator"``).  String matching is case-insensitive.

    Args:
        profile: A `ProfileType` enum member or its string value.
    Returns:
        The matching `ProfileType` member.
    Raises:
        `InvalidProfileName` error:
            If *profile* is a string that does not match any
            ``ProfileType`` value.
    Example::
        normalise_profile_name("observer")           # → ProfileType.OBSERVER
        normalise_profile_name(ProfileType.AGENT)    # → ProfileType.AGENT (pass-through)
        normalise_profile_name("ghost")              # → raises InvalidProfileName
    """

    # Lazy loaded so no runtime funny business
    from logger_lab.core.enums import ProfileType

    if isinstance(profile, ProfileType):
        return profile

    try:
        return ProfileType(profile.lower())

    except ValueError:
        raise InvalidProfileName(profile)


# File-system helpers
def get_log_dir(path: Path | str = Path("logs")) -> Path:
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
