"""
logger-lab: composable Python logging, reimagined as a system.

`lab()` is the one way to build a logger. Start from a profile, or compose the four kinds of
building block yourself: outputs, features, formats and catalysts. Then call ``build(name)``::

    from logger_lab import lab

    logger = lab().with_profile("investigator").build(__name__)  # console + logs/app.log

    # The same, with the file rolled over daily at 02:00
    nightly = lab().with_profile("investigator").with_feature("TIMED", at="02:00").build("nightly")

``__version__`` is the installed version, read from the package metadata.
"""

import importlib.metadata

from logger_lab.core.builder import LabBuilder, lab
from logger_lab.core.enums import Catalyst, Day, Feature, Format, Kind, Output, ProfileType, TheoryType, Unit
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
from logger_lab.logging_kernel.dispatch import drain
from logger_lab.logging_kernel.formatters import log_event

__version__ = importlib.metadata.version("logger-lab")  # pyproject.toml is the one place the version is written

__all__ = [
    # the composer
    "lab",
    "LabBuilder",
    # names
    "Kind",
    "Output",
    "Feature",
    "Format",
    "Catalyst",
    "ProfileType",
    "TheoryType",
    # TIMED option values
    "Unit",
    "Day",
    # structured logging helper
    "log_event",
    # async: wait until queued records are written
    "drain",
    # error hierarchy: root
    "LabError",
    # error hierarchy: registry
    "LabRegistryError",
    "InvalidNameError",
    "TheoryNotFoundError",
    "RegistrationError",
    # error hierarchy: configuration
    "LabConfigurationError",
    "InvalidLevelError",
    "CompositionError",
    "HandlerConfigurationError",
    "LogDirectoryError",
    "LogFileClashError",
    # error hierarchy: builder
    "BuilderError",
    # warnings
    "ProfileSuggestionWarning",
    "SharedFileSettingsWarning",
]
