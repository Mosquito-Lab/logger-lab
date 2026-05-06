"""
``core`` — registry, builder, and enumeration types for logger-lab.

Exports the public surface of all three core submodules so callers can
import from ``logger_lab.core`` without knowing the internal layout::

    from logger_lab.core import lab, ExperimentType, ProfileType
    from logger_lab.core import EXPERIMENTS, PROFILES, get_experiment, get_profile
"""

from logger_lab.core.builder   import LabBuilder, lab
from logger_lab.core.enums     import ExperimentType, ProfileType, TheoryType
from logger_lab.core.registry  import EXPERIMENTS, PROFILES, get_experiment, get_profile

__all__ = [
    # builder
    "LabBuilder", "lab",
    # enums
    "ExperimentType", "ProfileType", "TheoryType",
    # registry
    "EXPERIMENTS","PROFILES",
    "get_experiment", "get_profile",
]
