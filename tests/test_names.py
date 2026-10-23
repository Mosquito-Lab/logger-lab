"""Names: every member of every kind resolves by member or value string, and a bad name says what is valid."""

import logging

import pytest

from logger_lab import (
    Catalyst, Feature, Format, InvalidNameError, Output, ProfileType, TheoryNotFoundError, TheoryType, lab,
)
from logger_lab.core.registry import THEORIES
from logger_lab.logging_kernel import clear_handlers, normalize_name

KINDS = [(Output, "output"), (Feature, "feature"), (Format, "format"), (Catalyst, "catalyst"),
         (ProfileType, "profile"), (TheoryType, "theory")]


@pytest.mark.parametrize(("enum_type", "kind"), KINDS, ids=[kind for _, kind in KINDS])
def test_every_member_resolves_by_member_value_and_lower_case(enum_type, kind):
    """The member, its value string and the lower-case value all resolve to the member."""

    for member in enum_type:
        for spelling in (member, member.value, member.value.lower()):
            assert normalize_name(enum_type, spelling, kind) is member


def built(builder, name: str) -> list[logging.Handler]:
    """Build *builder* into *name*, return its handlers, and release them (so the next build can reuse the file)."""

    logger = builder.build(name)
    handlers = list(logger.handlers)
    clear_handlers(logger)

    return handlers


def test_every_building_block_and_profile_builds():
    """Each member of each kind builds on the smallest composition it needs."""

    for output in Output:
        builder = lab().with_output(output.value.lower())
        assert built(builder.with_subscriber(print) if output is Output.RELAY else builder, f"n.{output.value}")

    for feature in Feature:
        assert len(built(lab().with_profile("investigator").with_feature(feature.value), f"n.{feature.value}")) == 2

    for format_ in Format:
        assert built(lab().with_output("console").with_format(format_.value.lower()), f"n.{format_.value}")

    for catalyst in Catalyst:
        assert built(lab().with_output("console").with_catalyst(catalyst), f"n.{catalyst.value}")

    for profile in ProfileType:
        assert built(lab().with_profile(profile.value.lower()), f"n.{profile.value}")


def test_a_member_name_that_differs_from_its_value_is_not_an_alias():
    """``"AGENT"`` and ``"CONSPIRATOR"`` are rejected. The value string is the alias."""

    for name, value in (("AGENT", "AI_AGENT"), ("CONSPIRATOR", "CONSPIRACY_THEORIST")):
        with pytest.raises(InvalidNameError, match=value):
            lab().with_profile(name)


@pytest.mark.parametrize(("call", "kind", "valid"), [
    (lambda: lab().with_output("printer"), "output", "CONSOLE, FILE, RELAY"),
    (lambda: lab().with_output("ROTATING"), "output", "CONSOLE, FILE, RELAY"),
    (lambda: lab().with_feature("ROTATING_FILE"), "feature", "MINIMAL, VERBOSE, ROTATING, TIMED"),
    (lambda: lab().with_format("xml"), "format", "RICH, TEXT, JSON"),
    (lambda: lab().with_catalyst("sync"), "catalyst", "ASYNC"),
    (lambda: lab().with_profile("ghost"), "profile", "CONSPIRACY_THEORIST"),
    (lambda: lab().with_theory("ghost"), "theory", "THROTTLE"),
    (lambda: lab().with_feature("MINIMAL", on="printer"), "output", "CONSOLE, FILE, RELAY"),
], ids=["unknown output", "a feature as an output", "a removed experiment name", "format", "catalyst",
        "profile", "theory", "on="])
def test_a_bad_name_says_its_kind_and_the_valid_names(call, kind, valid):
    """Each method takes only its own kind. The error names the kind and lists what is valid."""

    with pytest.raises(InvalidNameError, match=f"not a recognized {kind} name.*{valid}") as err:
        call()

    assert err.value.kind == kind


def test_a_placeholder_theory_fails_as_a_placeholder():
    """Every theory not yet registered raises `TheoryNotFoundError`, never a bad-name error."""

    for theory in TheoryType:
        if theory not in THEORIES:
            with pytest.raises(TheoryNotFoundError, match="placeholder"):
                lab().with_profile("investigator").with_theory(theory.value.lower())
