"""Every experiment, profile and theory is selectable by enum member or value string (Standards §2.8)."""

import pytest

from logger_lab import (
    ExperimentType, InvalidExperimentName, InvalidProfileName, InvalidTheoryName, ProfileType,
    TheoryNotFoundError, TheoryType, get_logger, lab,
)
from logger_lab.logging_kernel import normalize_exp_name, normalize_profile_name, normalize_theory_name

# Members whose *name* differs from their *value* — the name as a string is not an alias.
RENAMED = [
    (ExperimentType.ROTATING_FILE, "ROTATING_FILE"),
    (ProfileType.AGENT, "AGENT"),
    (ProfileType.CONSPIRATOR, "CONSPIRATOR"),
]


@pytest.mark.parametrize("member", list(ExperimentType))
@pytest.mark.parametrize("form", ["member", "value", "lower"])
def test_every_experiment_resolves_by_member_and_value(member, form):
    """`with_experiment()` and `get_logger()` accept the member, its value and its lowercase value."""

    name = {"member": member, "value": member.value, "lower": member.value.lower()}[form]

    assert normalize_exp_name(name) is member
    assert lab().with_experiment(name).plan() == [member]
    assert get_logger(f"names.exp.{member.value}.{form}", experiment=name).handlers


@pytest.mark.parametrize("member", list(ProfileType))
@pytest.mark.parametrize("form", ["member", "value", "lower"])
def test_every_profile_resolves_by_member_and_value(member, form):
    """`with_profile()` and `get_logger()` accept the member, its value and its lowercase value."""

    name = {"member": member, "value": member.value, "lower": member.value.lower()}[form]

    assert normalize_profile_name(name) is member
    assert lab().with_profile(name).plan()
    assert get_logger(f"names.prof.{member.value}.{form}", profile=name).handlers


@pytest.mark.parametrize("member", list(TheoryType))
@pytest.mark.parametrize("form", ["member", "value", "lower"])
def test_every_theory_resolves_by_member_and_value(member, form):
    """Theory names resolve both ways; unregistered theories then fail as placeholders, not as bad names."""

    name = {"member": member, "value": member.value, "lower": member.value.lower()}[form]

    assert normalize_theory_name(name) is member

    with pytest.raises(TheoryNotFoundError, match="placeholder"):
        get_logger(f"names.theory.{member.value}.{form}", theory=name)


@pytest.mark.parametrize(("member", "name"), RENAMED)
def test_member_name_string_is_not_an_alias(member, name):
    """``"ROTATING_FILE"``/``"AGENT"``/``"CONSPIRATOR"`` are rejected — the value string is the alias."""

    normalize = normalize_exp_name if isinstance(member, ExperimentType) else normalize_profile_name
    error = InvalidExperimentName if isinstance(member, ExperimentType) else InvalidProfileName

    with pytest.raises(error, match=member.value):
        normalize(name)


def test_invalid_names_list_the_valid_values():
    """Each name error says which names are valid."""

    with pytest.raises(InvalidExperimentName, match="ROTATING"):
        lab().with_experiment("rotating_file")
    with pytest.raises(InvalidProfileName, match="CONSPIRACY_THEORIST"):
        lab().with_profile("ghost")
    with pytest.raises(InvalidTheoryName, match="TIMED_FILE"):
        lab().with_theory("ghost")


def test_theory_member_is_rejected_by_with_experiment():
    """Theories go through `with_theory()`, not `with_experiment()`."""

    with pytest.raises(InvalidExperimentName):
        lab().with_experiment(TheoryType.TRACE)  # pyrefly: ignore[bad-argument-type]
