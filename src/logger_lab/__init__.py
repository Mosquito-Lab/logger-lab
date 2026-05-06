"""
logger-lab — composable Python logging, reimagined as a system.

Quick start
-----------

**Profiles** (prebuilt combinations)::

    from logger_lab import get_logger

    logger = get_logger(__name__, profile="investigator")
    logger.info("System online")

**Experiments** (single handler factories)::

    logger = get_logger(__name__, experiment="standard")

**Fluent builder** (custom composition)::

    from logger_lab import lab

    logger = (
        lab()
        .with_experiment("standard")
        .with_experiment("file")
        .with_level("DEBUG")
        .build(__name__)
    )

**Structured events** (AI / machine-readable output)::

    from logger_lab import get_logger, log_event
    import logging

    logger = get_logger(__name__, profile="ai_agent")
    log_event(
        logger, logging.INFO, "Inference complete",
        event="inference_done",
        context={"tokens": 512},
    )
"""

from logging import DEBUG, Logger

from logger_lab.core import TheoryType
from logger_lab.core.builder import LabBuilder, lab
from logger_lab.core.enums import ExperimentType, ProfileType
from logger_lab.core.registry import get_experiment, get_profile
from logger_lab.logging_kernel.errors import (
    BuilderError,
    ExperimentNotFoundError,
    ExperimentRegistrationError,
    HandlerConfigurationError,
    InvalidExperimentName,
    InvalidLevelError,
    InvalidProfileName,
    LabConfigurationError,
    LabError,
    LabRegistryError,
    LogDirectoryError,
    ProfileNotFoundError,
    ProfileRegistrationError,
)
from logger_lab.logging_kernel.formatters import log_event
from logger_lab.logging_kernel.handlers import (
    normalise_exp_name,
    normalise_level_name,
    normalise_profile_name,
)

__all__ = [
    # primary entry points
    "get_logger",
    "lab",
    # types
    "ExperimentType",
    "ProfileType",
    "LabBuilder",
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
    # error hierarchy — configuration
    "LabConfigurationError",
    "InvalidLevelError",
    "HandlerConfigurationError",
    "LogDirectoryError",
    "ExperimentRegistrationError",
    "ProfileRegistrationError",
    # error hierarchy — builder
    "BuilderError",
]


def get_logger(
        name: str,
        *,
        theory: TheoryType | None = None,
        profile: ProfileType | str | None = None,
        experiment: ExperimentType | str | None = None,
        level: int | str = DEBUG,
) -> Logger:
    """
    Return a configured `logging.Logger` in one call.

    Exactly one of *profile* or *experiment* should be supplied.  If
    both are provided the profile is applied first and the experiment
    layered on top.  If neither is supplied `BuilderError` is raised.

    Args:
        name:       Logger name, typically ``__name__``.
        theory:     Theory identifier — `TheoryType` member.
        profile:    Profile identifier — `ProfileType` member or
                    its string alias (e.g. ``"investigator"``).
        experiment: Experiment identifier — `ExperimentType`
                    member or its string alias (e.g. ``"standard"``).
        level:      Logging level — string name or integer constant.
                    Defaults to `logging.DEBUG`.
    Returns:
        A configured `logging.Logger` with ``propagate = False``.
    Raises:
        `BuilderError`:
            If neither *profile* nor *experiment* is supplied.
        `InvalidExperimentName`:
            If *experiment* is an unrecognised string.
        `InvalidProfileName`:
            If *profile* is an unrecognised string.
        `ExperimentNotFoundError`:
            If a valid enum value has no registered factory.
        `ProfileNotFoundError`:
            If a valid enum value has no registered factory.
    Examples::
        logger = get_logger(__name__, profile="investigator")
        logger = get_logger(__name__, experiment="AI", level="INFO")
        logger = get_logger(__name__, profile=ProfileType.OBSERVER)
    """

    # Initialize the builder
    builder = lab().with_level(level)

    if theory is not None:
        builder = builder.with_experiment(theory)

    if profile is not None:
        builder = builder.with_profile(profile)

    if experiment is not None:
        builder = builder.with_experiment(experiment)

    return builder.build(name)
