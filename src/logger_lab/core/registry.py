"""
Central registry: the built-in building blocks and profiles, and the theories in trial.

``OUTPUTS``, ``FEATURES``, ``FORMATS`` and ``CATALYSTS`` map each kind's enum members to their
specs, and ``PROFILES`` maps profiles to recipes. They are plain tables, written out below.
The tests pin that every spec is well formed: its member matches its key, a feature fits an
output, and an output accepts its default format. They also plan every profile
(``tests/test_registry.py``, ``tests/test_composition.py``).

``THEORIES`` is the one table filled at runtime, through `register_theory`, which checks
each spec as it comes in. Lookups (`spec_for`, `get_theory`, `get_profile`) raise typed
errors instead of ``KeyError``.
"""

from logger_lab.catalysts.asynchronous import ASYNC_SPEC
from logger_lab.core.enums import Catalyst, Feature, Format, Kind, Output, ProfileType, TheoryType
from logger_lab.core.specs import CatalystSpec, FeatureSpec, FormatSpec, OutputSpec, ProfileSpec
from logger_lab.features.detail import MINIMAL_SPEC, VERBOSE_SPEC
from logger_lab.features.rotation import ROTATING_SPEC, TIMED_SPEC
from logger_lab.formats import JSON_SPEC, RICH_SPEC, TEXT_SPEC
from logger_lab.logging_kernel.errors import RegistrationError, TheoryNotFoundError
from logger_lab.outputs.console import CONSOLE_SPEC
from logger_lab.outputs.file import FILE_SPEC
from logger_lab.outputs.relay import RELAY_SPEC
from logger_lab.profiles import PROFILE_SPECS

Spec = OutputSpec | FeatureSpec | FormatSpec | CatalystSpec  # Any building block's spec


##############
# The tables #
##############

OUTPUTS: dict[Output, OutputSpec] = {
    Output.CONSOLE: CONSOLE_SPEC,
    Output.FILE: FILE_SPEC,
    Output.RELAY: RELAY_SPEC,
}

FEATURES: dict[Feature, FeatureSpec] = {
    Feature.MINIMAL: MINIMAL_SPEC,
    Feature.VERBOSE: VERBOSE_SPEC,
    Feature.ROTATING: ROTATING_SPEC,
    Feature.TIMED: TIMED_SPEC,
}

FORMATS: dict[Format, FormatSpec] = {
    Format.RICH: RICH_SPEC,
    Format.TEXT: TEXT_SPEC,
    Format.JSON: JSON_SPEC,
}

CATALYSTS: dict[Catalyst, CatalystSpec] = {
    Catalyst.ASYNC: ASYNC_SPEC,
}

PROFILES: dict[ProfileType, ProfileSpec] = {spec.member: spec for spec in PROFILE_SPECS}

THEORIES: dict[TheoryType, tuple[Kind, Spec]] = {}  # Filled by register_theory(); every theory is a placeholder today

SPEC_TYPES: dict[Kind, type[OutputSpec] | type[FeatureSpec] | type[FormatSpec] | type[CatalystSpec]] = {
    Kind.OUTPUT: OutputSpec,
    Kind.FEATURE: FeatureSpec,
    Kind.FORMAT: FormatSpec,
    Kind.CATALYST: CatalystSpec,
}  # The spec type each kind of theory must have


############
# Theories #
############

def register_theory(kind: Kind, spec: Spec) -> None:
    """
    Register a working theory as a building block of *kind* (the trial stage, Standards §3.4).

    An unregistered `TheoryType` is a placeholder and raises `TheoryNotFoundError` when
    selected. The spec is checked here, because a theory is added at runtime, while it is
    being tried out.

    Raises:
        `RegistrationError`: If *spec* isn't the spec type of *kind*, its member isn't a
        `TheoryType`, its ``build`` isn't callable, or it fits no output.
    Example::
        register_theory(Kind.FEATURE, FeatureSpec(TheoryType.THROTTLE, fits=frozenset({Output.RELAY})))
    """

    member = getattr(spec, "member", spec)
    spec_type = SPEC_TYPES[kind]

    if not isinstance(spec, spec_type):
        raise RegistrationError(member, f"registered as {kind.value}, its spec must be {spec_type.__name__}")

    if not isinstance(member, TheoryType):
        raise RegistrationError(member, "its member must be a TheoryType")

    if isinstance(spec, (OutputSpec, CatalystSpec)) and not callable(spec.build):
        raise RegistrationError(member, "build is not callable")

    if isinstance(spec, (FeatureSpec, FormatSpec)) and not spec.fits:
        raise RegistrationError(member, "it must fit at least one output")

    THEORIES[member] = (kind, spec)


###########
# Lookups #
###########

def spec_for(member: Output | Feature | Format | Catalyst) -> Spec:
    """Return the spec of a built-in *member* of any kind."""

    spec: Spec | None = None

    if isinstance(member, Output):
        spec = OUTPUTS.get(member)
    elif isinstance(member, Feature):
        spec = FEATURES.get(member)
    elif isinstance(member, Format):
        spec = FORMATS.get(member)
    elif isinstance(member, Catalyst):
        spec = CATALYSTS.get(member)

    if spec is None:
        raise RegistrationError(member, "nothing is registered for it")

    return spec


def get_theory(theory: TheoryType) -> tuple[Kind, Spec]:
    """
    Return the kind and spec registered for *theory*.

    Raises:
        `TheoryNotFoundError`: If *theory* is still a placeholder (nothing registered).
    """

    if theory not in THEORIES:
        raise TheoryNotFoundError(theory)

    return THEORIES[theory]


def get_profile(profile: ProfileType) -> ProfileSpec:
    """
    Return the spec of *profile*.

    Raises:
        `RegistrationError`: If no recipe is registered for it.
    """

    if profile not in PROFILES:
        raise RegistrationError(profile, "no profile recipe is registered for it")

    return PROFILES[profile]
