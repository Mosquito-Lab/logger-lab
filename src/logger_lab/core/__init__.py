"""
``core``: registry, builder, specs and enumeration types for logger-lab.

Exports the public surface of the core submodules so callers can import from
``logger_lab.core`` without knowing the internal layout::

    from logger_lab.core import lab, Output, Feature, Format, Catalyst, ProfileType
    from logger_lab.core import OUTPUTS, FEATURES, register_theory, FeatureSpec
"""

from logger_lab.core.builder   import Composition, LabBuilder, PlannedOutput, lab
from logger_lab.core.enums     import Catalyst, Day, Feature, Format, Kind, Output, ProfileType, TheoryType, Unit
from logger_lab.core.registry  import (
    CATALYSTS, FEATURES, FORMATS, OUTPUTS, PROFILES, THEORIES,
    get_profile, get_theory, register_theory, spec_for,
)
from logger_lab.core.specs     import CatalystSpec, FeatureSpec, FormatSpec, OutputPlan, OutputSpec, ProfileSpec

__all__ = [
    # builder
    "LabBuilder", "lab", "Composition", "PlannedOutput",
    # enums
    "Kind", "Output", "Feature", "Format", "Catalyst", "ProfileType", "TheoryType", "Unit", "Day",
    # registry
    "OUTPUTS", "FEATURES", "FORMATS", "CATALYSTS", "PROFILES", "THEORIES",
    "get_profile", "get_theory", "spec_for", "register_theory",
    # specs
    "OutputSpec", "FeatureSpec", "FormatSpec", "CatalystSpec", "ProfileSpec", "OutputPlan",
]
