"""
``logging_kernel`` — low-level infrastructure for logger-lab.

Exports every utility that experiments, profiles, and the builder need
so they can import from a single namespace::
"""

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
from logger_lab.logging_kernel.formatters import (
    JSONFormatter,
    build_console_formatter,
    build_file_formatter,
    log_event,
)
from logger_lab.logging_kernel.handlers import (
    LAB_HANDLERS,
    SHARED_FILES,
    SharedFileHandler,
    SharedRotatingFileHandler,
    StayClosedMixin,
    configure_handler,
    clear_handlers,
    file_key,
    get_log_dir,
    install_handlers,
    release_handler,
    share_file_handler,
)
from logger_lab.logging_kernel.normalizers import (
    normalize_profile_name,
    normalize_level_name,
    normalize_exp_name,
    normalize_theory_name,
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
    "TheoryNotFoundError",
    "InvalidTheoryName",
    # configuration errors
    "LabConfigurationError",
    "InvalidLevelError",
    "HandlerConfigurationError",
    "LogDirectoryError",
    "ExperimentClashError",
    "LogFileClashError",
    "ExperimentRegistrationError",
    "ProfileRegistrationError",
    # builder errors
    "BuilderError",
    # warnings
    "DuplicateExperimentWarning",
    "SharedFileSettingsWarning",
    # formatters
    "log_event",
    "JSONFormatter",
    "build_file_formatter",
    "build_console_formatter",
    # handler utilities
    "get_log_dir",
    "clear_handlers",
    "configure_handler",
    "file_key",
    "install_handlers",
    "release_handler",
    "share_file_handler",
    "LAB_HANDLERS",
    "SHARED_FILES",
    "SharedFileHandler",
    "SharedRotatingFileHandler",
    "StayClosedMixin",
    # normalizers
    "normalize_exp_name",
    "normalize_level_name",
    "normalize_profile_name",
    "normalize_theory_name",
]
