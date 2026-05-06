"""
``logging_kernel`` — low-level infrastructure for logger-lab.

Exports every utility that experiments, profiles, and the builder need
so they can import from a single namespace::
"""

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
from logger_lab.logging_kernel.formatters import (
    JSONFormatter,
    build_console_formatter,
    build_file_formatter,
    log_event,
)
from logger_lab.logging_kernel.handlers import (
    configure_handler,
    clear_handlers,
    get_log_dir,
    normalise_exp_name,
    normalise_level_name,
    normalise_profile_name,
)

__all__ = [
    # root
    "LabError",
    # registry errors
    "LabRegistryError",
    "ExperimentNotFoundError",
    "ProfileNotFoundError",
    "InvalidExperimentName",
    "InvalidProfileName",
    # configuration errors
    "LabConfigurationError",
    "InvalidLevelError",
    "HandlerConfigurationError",
    "LogDirectoryError",
    "ExperimentRegistrationError",
    "ProfileRegistrationError",
    # builder errors
    "BuilderError",
    # formatters
    "JSONFormatter",
    "build_file_formatter",
    "build_console_formatter",
    "log_event",
    # handler utilities
    "clear_handlers",
    "configure_handler",
    "normalise_level_name",
    "normalise_exp_name",
    "normalise_profile_name",
    "get_log_dir",
]
