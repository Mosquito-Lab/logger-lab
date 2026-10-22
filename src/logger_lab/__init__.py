"""
logger-lab — composable Python logging, reimagined as a system.

`lab()` is the one way to build a logger: queue a profile, experiments and theories,
set the level and file args, then ``build(name)``::

    from logger_lab import lab

    logger = lab().with_profile("investigator").build(__name__)
"""

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
from logger_lab.logging_kernel.dispatch import drain
from logger_lab.logging_kernel.formatters import log_event

__all__ = [
    # the composer
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
    # async: wait until queued records are written
    "drain",
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

