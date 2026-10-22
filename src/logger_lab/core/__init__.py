"""
``core`` — registry, builder, and enumeration types for logger-lab.

Exports the public surface of all three core submodules so callers can
import from ``logger_lab.core`` without knowing the internal layout::

    from logger_lab.core import lab, ExperimentType, ProfileType
    from logger_lab.core import EXPERIMENTS, PROFILES, get_experiment, get_profile
"""

from logger_lab.core.builder   import LabBuilder, lab
from logger_lab.core.enums     import Channel, ExperimentType, ProfileType, TheoryType
from logger_lab.core.registry  import (
    CHANNELS, EXPERIMENTS, PROFILE_EXPERIMENTS, PROFILES, THEORIES,
    find_channel_clash, get_channel, get_experiment, get_profile, get_profile_experiments, get_theory,
    register_experiment, register_profile, register_theory,
)

__all__ = [
    # builder
    "LabBuilder", "lab",
    # enums
    "Channel", "ExperimentType", "ProfileType", "TheoryType",
    # registry
    "CHANNELS", "EXPERIMENTS", "PROFILE_EXPERIMENTS", "PROFILES", "THEORIES",
    "find_channel_clash", "get_channel", "get_experiment", "get_profile",
    "get_profile_experiments", "get_theory",
    "register_experiment", "register_profile", "register_theory",
]
