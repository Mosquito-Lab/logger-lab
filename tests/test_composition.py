"""The builder's composition rules: one experiment per channel, duplicates warn and keep the first."""

import logging

import pytest
from rich.logging import RichHandler

from logger_lab import (
    BuilderError, Channel, DuplicateExperimentWarning, ExperimentClashError, ExperimentType, ProfileType,
    get_logger, lab,
)
from logger_lab.core.registry import CHANNELS, find_channel_clash
from logger_lab.logging_kernel import SharedFileHandler, SharedRotatingFileHandler

CONSOLE = [ExperimentType.STANDARD, ExperimentType.VERBOSE, ExperimentType.MINIMALIST]
FILES = [ExperimentType.FILE, ExperimentType.ROTATING_FILE]


def test_every_experiment_has_a_channel():
    """Console, file and JSON experiments are registered on the channel they write to."""

    assert {e: CHANNELS[e] for e in ExperimentType} == {
        ExperimentType.STANDARD: Channel.CONSOLE,
        ExperimentType.VERBOSE: Channel.CONSOLE,
        ExperimentType.MINIMALIST: Channel.CONSOLE,
        ExperimentType.FILE: Channel.FILE,
        ExperimentType.ROTATING_FILE: Channel.FILE,
        ExperimentType.AI: Channel.JSON,
    }


@pytest.mark.parametrize("group", [CONSOLE, FILES], ids=["console", "file"])
def test_two_experiments_on_one_channel_clash(group):
    """Any two different experiments on the same channel raise, naming both and the rule."""

    for first in group:
        for second in group:
            if first is second:
                continue

            with pytest.raises(ExperimentClashError, match="at most one experiment per channel") as err:
                lab().with_experiment(first).with_experiment(second).build("clash")

            assert f"'{first.value}' (queued)" in str(err.value)
            assert f"'{second.value}' (queued)" in str(err.value)


def test_profile_and_experiment_clash_names_the_profile():
    """`investigator` already owns the console and file channels."""

    with pytest.raises(ExperimentClashError, match=r"'ROTATING' \(queued\) clashes with 'FILE' \(from profile 'INVESTIGATOR'\)"):
        lab().with_profile("investigator").with_experiment("ROTATING").build("clash")

    with pytest.raises(ExperimentClashError, match="CONSOLE"):
        get_logger("clash2", profile="investigator", experiment="minimalist")


def test_one_of_each_channel_composes():
    """A console, a file and a JSON experiment build together, in queue order."""

    logger = lab().with_profile("investigator").with_experiment("AI").build("full")

    assert [type(h) for h in logger.handlers] == [RichHandler, SharedFileHandler, logging.StreamHandler]


def test_duplicate_experiment_warns_and_keeps_first():
    """The same experiment twice is a duplicate, not a clash."""

    with pytest.warns(DuplicateExperimentWarning, match="'FILE' is queued twice"):
        logger = lab().with_experiment("FILE").with_experiment(ExperimentType.FILE).build("dup")

    assert len(logger.handlers) == 1


def test_profile_plus_its_own_experiment_warns():
    """Queueing an experiment a profile already has warns once and builds it once."""

    with pytest.warns(DuplicateExperimentWarning, match="from profile 'INVESTIGATOR', then queued"):
        plan = lab().with_profile("investigator").with_experiment("FILE").plan()

    assert plan == [ExperimentType.STANDARD, ExperimentType.FILE]


def test_clash_leaves_an_existing_logger_untouched():
    """A rejected composition raises before the old handlers are cleared."""

    logger = lab().with_experiment("minimalist").build("keep")
    handler = logger.handlers[0]

    with pytest.raises(ExperimentClashError):
        lab().with_experiment("minimalist").with_experiment("verbose").build("keep")

    assert logger.handlers == [handler]


def test_empty_builder_raises():
    """Nothing queued is a `BuilderError`."""

    with pytest.raises(BuilderError):
        lab().build("empty")


@pytest.mark.parametrize("profile", list(ProfileType))
def test_profiles_never_clash_internally(profile):
    """Every registered profile is a clash-free composition."""

    assert find_channel_clash(lab().with_profile(profile).plan()) is None


def test_conspiracy_theorist_is_verbose_plus_rotating_only():
    """Step 1: `rotating_file` replaces `file` — no second handler on the same file."""

    logger = get_logger("ct", profile="conspiracy_theorist")

    assert [type(h) for h in logger.handlers] == [logging.StreamHandler, SharedRotatingFileHandler]
