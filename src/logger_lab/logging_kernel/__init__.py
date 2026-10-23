"""
``logging_kernel``: low-level infrastructure for logger-lab.

Exports every utility that outputs, features, formats, catalysts and the builder need
so they can import from a single namespace.
"""

from logger_lab.logging_kernel.errors import (
    BuilderError,
    CompositionError,
    HandlerConfigurationError,
    InvalidLevelError,
    InvalidNameError,
    LabConfigurationError,
    LabError,
    LabRegistryError,
    LogDirectoryError,
    LogFileClashError,
    ProfileSuggestionWarning,
    RegistrationError,
    SharedFileSettingsWarning,
    TheoryNotFoundError,
)
from logger_lab.logging_kernel.formatters import (
    DATE_FORMAT,
    TEXT_LAYOUTS,
    JSONFormatter,
    log_event,
    text_formatter,
)
from logger_lab.logging_kernel.dispatch import (
    AsyncHandler,
    drain,
    stop_worker,
)
from logger_lab.logging_kernel.handlers import (
    LAB_HANDLERS,
    SHARED_FILES,
    LabFileHandler,
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
    level_names,
    normalize_level_name,
    normalize_name,
)
from logger_lab.logging_kernel.rollover import (
    DAYS,
    UNITS,
    SizeRule,
    TimeRule,
)

__all__ = [
    # root
    "LabError",
    # registry errors
    "LabRegistryError",
    "InvalidNameError",
    "TheoryNotFoundError",
    "RegistrationError",
    # configuration errors
    "LabConfigurationError",
    "InvalidLevelError",
    "CompositionError",
    "HandlerConfigurationError",
    "LogDirectoryError",
    "LogFileClashError",
    # builder errors
    "BuilderError",
    # warnings
    "ProfileSuggestionWarning",
    "SharedFileSettingsWarning",
    # formatters
    "log_event",
    "JSONFormatter",
    "text_formatter",
    "TEXT_LAYOUTS",
    "DATE_FORMAT",
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
    "LabFileHandler",
    "StayClosedMixin",
    # rollover
    "DAYS",
    "UNITS",
    "SizeRule",
    "TimeRule",
    # dispatch
    "AsyncHandler",
    "drain",
    "stop_worker",
    # normalizers
    "level_names",
    "normalize_level_name",
    "normalize_name",
]
