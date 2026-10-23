"""The registry's tables are well formed, every profile composes, and theories act as the kind they register as."""

import importlib
import logging
import re
from pathlib import Path

import pytest

import logger_lab
from logger_lab import (
    CompositionError, Feature, Format, Kind, Output, ProfileType, RegistrationError, TheoryNotFoundError,
    TheoryType, lab,
)
from logger_lab.core import registry
from logger_lab.core.registry import (
    CATALYSTS, FEATURES, FORMATS, OUTPUTS, PROFILES, get_profile, get_theory, register_theory,
)
from logger_lab.core.specs import CatalystSpec, FeatureSpec, FormatSpec, OutputSpec

TABLES = [(OUTPUTS, Output, OutputSpec), (FEATURES, Feature, FeatureSpec), (FORMATS, Format, FormatSpec)]


#######################
# The built-in tables #
#######################

def test_every_member_has_a_spec_of_its_kind_under_its_own_key():
    """Each table covers its whole enum, and each spec is the right type and sits under its own member."""

    for table, enum_type, spec_type in [*TABLES, (CATALYSTS, type(next(iter(CATALYSTS))), CatalystSpec)]:
        assert set(table) == set(enum_type)

        for member, spec in table.items():
            assert isinstance(spec, spec_type) and spec.member is member

    assert set(PROFILES) == set(ProfileType)
    assert all(spec.member is member for member, spec in PROFILES.items())


def test_the_specs_agree_with_each_other():
    """
    Every feature and format fits an output. An output's default format is one it renders,
    and a format fits exactly the outputs that render it.
    """

    for spec in [*FEATURES.values(), *FORMATS.values()]:
        assert spec.fits, spec.member

    for output, spec in OUTPUTS.items():
        assert spec.default_format is None or spec.default_format in spec.formats, output
        assert callable(spec.build)

    for format_, spec in FORMATS.items():
        assert spec.fits == {output for output, output_spec in OUTPUTS.items() if format_ in output_spec.formats}

    assert all(callable(spec.build) for spec in CATALYSTS.values())


def test_every_profile_composes():
    """Every recipe plans without breaking a rule (its exact composition: test_composition)."""

    for profile in ProfileType:
        assert lab().with_profile(profile).plan().outputs


def test_the_version_is_the_one_in_pyproject():
    """PK-10: ``__version__`` comes from the package metadata, so it can't drift from ``pyproject.toml``."""

    pyproject = (Path(__file__).parents[1] / "pyproject.toml").read_text(encoding="utf-8")

    match = re.search(r'^version = "(.+)"$', pyproject, re.MULTILINE)

    assert match is not None and match.group(1) == logger_lab.__version__


def test_lookups_raise_typed_errors(monkeypatch):
    """An unregistered theory is a placeholder; a profile with no recipe is a RegistrationError, not a KeyError."""

    with pytest.raises(TheoryNotFoundError, match="'TRACE' is still a placeholder"):
        get_theory(TheoryType.TRACE)

    monkeypatch.setattr(registry, "PROFILES", {})

    with pytest.raises(RegistrationError, match="no profile recipe"):
        get_profile(ProfileType.GUI)


############
# Theories #
############

@pytest.mark.parametrize(("kind", "spec", "match"), [
    (Kind.OUTPUT, FeatureSpec(TheoryType.TRACE, fits=frozenset({Output.CONSOLE})),
     "OUTPUT, its spec must be OutputSpec"),
    (Kind.FEATURE, FEATURES[Feature.MINIMAL], "its member must be a TheoryType"),
    (Kind.FEATURE, FeatureSpec(TheoryType.TRACE, fits=frozenset()), "fit at least one output"),
    (Kind.OUTPUT, OutputSpec(TheoryType.DB, build="nope"), "not callable"),  # pyrefly: ignore[bad-argument-type]
], ids=["wrong spec type", "a built-in member", "fits nothing", "build not callable"])
def test_register_theory_checks_the_spec(kind, spec, match):
    """A theory is added at runtime, so its spec is checked as it comes in."""

    with pytest.raises(RegistrationError, match=match):
        register_theory(kind, spec)


def test_every_theory_has_an_idea_file_that_names_its_kind():
    """TH-6: each TheoryType has an idea file, ``theories/<name>_exp.py``, that states its likely kind (§3.4)."""

    for theory in TheoryType:
        module = importlib.import_module(f"logger_lab.theories.{theory.value.lower()}_exp")

        assert "\nKind: " in (module.__doc__ or ""), theory


@pytest.fixture
def theories(monkeypatch):
    """An empty theory table for one test."""

    monkeypatch.setattr(registry, "THEORIES", {})

    return registry.THEORIES


def test_feature_theory_attaches_like_a_feature(theories):
    """A feature theory follows the feature rules: it fits outputs, takes options, and honors on=."""

    register_theory(Kind.FEATURE, FeatureSpec(TheoryType.THROTTLE, fits=frozenset({Output.CONSOLE}),
                                              options={"per_second": 10}))

    names = lab().with_profile("investigator").with_theory("throttle", per_second=20).plan().names()

    assert names["CONSOLE"]["features"] == ["THROTTLE"] and names["FILE"]["features"] == []

    with pytest.raises(CompositionError, match="'THROTTLE' works on console outputs, not file"):
        lab().with_profile("investigator").with_theory("THROTTLE", on="file").plan()
    with pytest.raises(CompositionError, match="has no option 'burst'"):
        lab().with_profile("investigator").with_theory("THROTTLE", burst=3).plan()


def test_output_theory_builds_like_an_output(theories):
    """An output theory is built from its own spec, with its options merged over its defaults."""

    seen: dict[str, object] = {}

    def build(plan) -> list[logging.Handler]:
        """Record the options it was built with."""

        seen.update(plan.options)

        return [logging.NullHandler()]

    register_theory(Kind.OUTPUT, OutputSpec(TheoryType.DB, build=build, options={"table": "logs", "batch": 50}))

    logger = lab().with_theory("DB", batch=10).build("theory.db")

    assert seen == {"table": "logs", "batch": 10}
    assert [type(h) for h in logger.handlers] == [logging.NullHandler]


def test_catalyst_theory_wraps_the_outputs(theories):
    """A catalyst theory receives the built outputs and returns the logger's handlers."""

    wrapped: list[list[logging.Handler]] = []

    def build(handlers, *, logger_name, options) -> list[logging.Handler]:
        """Record what it wraps, change nothing."""

        wrapped.append(handlers)

        return handlers

    register_theory(Kind.CATALYST, CatalystSpec(TheoryType.PROCESS, build=build, group="dispatch"))

    lab().with_profile("observer").with_theory("PROCESS").build("theory.proc")

    assert len(wrapped) == 1 and len(wrapped[0]) == 1

    with pytest.raises(CompositionError, match="'ASYNC' and 'PROCESS' are both dispatch catalysts"):
        lab().with_profile("gui").with_theory("PROCESS").plan()


def test_on_is_refused_for_a_theory_that_cannot_use_it(theories):
    """CR-13: on= was silently ignored for an output or catalyst theory. It only applies to features and formats."""

    register_theory(Kind.OUTPUT, OutputSpec(TheoryType.DB, build=lambda plan: []))
    register_theory(Kind.CATALYST, CatalystSpec(TheoryType.PROCESS, build=lambda handlers, **_: handlers))

    with pytest.raises(CompositionError, match="'DB' is an output theory, so on= doesn't apply to it"):
        lab().with_theory("DB", on="file")
    with pytest.raises(CompositionError, match="'PROCESS' is a catalyst theory"):
        lab().with_profile("observer").with_theory("PROCESS", on="console")


def test_an_output_refuses_a_format_it_cannot_render(theories):
    """CR-17: a format theory that fits the console planned fine and would have been written as TEXT."""

    register_theory(Kind.FORMAT, FormatSpec(TheoryType.SEC, fits=frozenset({Output.CONSOLE})))

    expected = "the console output can't render the 'SEC' format; the formats it renders: JSON, RICH, TEXT"

    with pytest.raises(CompositionError, match=expected):
        lab().with_output("console").with_theory("SEC").plan()
