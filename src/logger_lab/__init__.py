""" logger-lab — composable Python logging, reimagined as a system """

from logging import DEBUG, Logger

from logger_lab.core.builder import LabBuilder, lab
from logger_lab.core.enums import Channel, ExperimentType, ProfileType, TheoryType
from logger_lab.core.registry import get_experiment, get_profile, get_theory
from logger_lab.logging_kernel.errors import (
    BuilderError,
    DuplicateExperimentWarning,
    ExperimentClashError,
    ExperimentNotFoundError,
    ExperimentRegistrationError,
    HandlerConfigurationError,
    InvalidExperimentName,
    InvalidLevelError,
    InvalidProfileName,
    InvalidTheoryName,
    LabConfigurationError,
    LabError,
    LabRegistryError,
    LogDirectoryError,
    LogFileClashError,
    ProfileNotFoundError,
    ProfileRegistrationError,
    SharedFileSettingsWarning,
    TheoryNotFoundError,
)
from logger_lab.logging_kernel.formatters import log_event

__all__ = [
    # primary entry points
    "get_logger",
    "lab",
    # types
    "ExperimentType",
    "ProfileType",
    "TheoryType",
    "Channel",
    "LabBuilder",
    # registry lookups
    "get_experiment",
    "get_profile",
    "get_theory",
    # structured logging helper
    "log_event",
    # error hierarchy — root
    "LabError",
    # error hierarchy — registry
    "LabRegistryError",
    "ExperimentNotFoundError",
    "ProfileNotFoundError",
    "InvalidExperimentName",
    "InvalidProfileName",
    "TheoryNotFoundError",
    "InvalidTheoryName",
    # error hierarchy — configuration
    "LabConfigurationError",
    "InvalidLevelError",
    "HandlerConfigurationError",
    "LogDirectoryError",
    "ExperimentClashError",
    "LogFileClashError",
    "ExperimentRegistrationError",
    "ProfileRegistrationError",
    # error hierarchy — builder
    "BuilderError",
    # warnings
    "DuplicateExperimentWarning",
    "SharedFileSettingsWarning",
]


def get_logger(
    name: str,
    *,
    theory: TheoryType | None = None,
    profile: ProfileType | str | None = None,
    experiment: ExperimentType | str | None = None,
    level: int | str = DEBUG
    ) -> Logger:
    """
    Return a configured `logging.Logger` in one call.

    Supply at least one of *profile*, *theory* or *experiment*; they combine
    in that order, under the builder's composition rules (one experiment per
    channel, duplicates warned and skipped).  If none is supplied
    `BuilderError` is raised.  For file args, use `lab()` directly.

    Args:
        name:       Logger name, typically ``__name__``.
        theory:     Theory identifier — `TheoryType` member or its
                    value string (e.g. ``"TIMED_FILE"``).
        profile:    Profile identifier — `ProfileType` member or
                    its string alias (e.g. ``"investigator"``).
        experiment: Experiment identifier — `ExperimentType`
                    member or its value string (e.g. ``"standard"``, ``"ROTATING"``).
        level:      Logging level — string name or integer constant.
                    Defaults to `logging.DEBUG`.
    Returns:
        A configured `logging.Logger` with ``propagate = False``.
    Raises:
        `BuilderError`:
            If no *profile*, *theory* or *experiment* is supplied.
        `ExperimentClashError`:
            If two of the requested experiments write to the same channel.
        `InvalidExperimentName`:
            If *experiment* is an unrecognized string.
        `InvalidProfileName`:
            If *profile* is an unrecognized string.
        `ExperimentNotFoundError`:
            If a valid enum value has no registered factory.
        `ProfileNotFoundError`:
            If a valid enum value has no registered factory.
        `TheoryNotFoundError`:
            If *theory* is still a placeholder.
    Examples::
        logger = get_logger(__name__, profile="investigator")
        logger = get_logger(__name__, experiment="AI", level="INFO")
        logger = get_logger(__name__, profile=ProfileType.OBSERVER)
    """

    # Initialize the builder
    builder = lab().with_level(level)

    if theory is not None:
        builder = builder.with_theory(theory)

    if profile is not None:
        builder = builder.with_profile(profile)

    if experiment is not None:
        builder = builder.with_experiment(experiment)

    return builder.build(name)
