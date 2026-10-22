"""Levels: what's accepted, what raises, and the default when none is set (INFO; WARNING with minimalist)."""

import logging
from pathlib import Path

import pytest

from logger_lab import InvalidLevelError, LogDirectoryError, lab
from logger_lab.core.builder import default_level
from logger_lab.core.enums import ExperimentType
from logger_lab.logging_kernel import get_log_dir, normalize_level_name


@pytest.mark.parametrize(("given", "expected"), [
    ("debug", logging.DEBUG), ("WARNING", logging.WARNING), ("warn", logging.WARNING),
    ("fatal", logging.CRITICAL), (logging.ERROR, logging.ERROR), (0, 0), (25, 25),
])
def test_accepted_levels(given, expected):
    """Names (case-insensitive, stdlib aliases too) and any integer 0 or above."""

    assert normalize_level_name(given) == expected


@pytest.mark.parametrize("given", ["DEBG", "LOUD", "", "10", -1, 2.5, True, None])
def test_rejected_levels_raise(given):
    """KN-2: no silent fallback to INFO — a typo or a wrong type raises, listing the valid names."""

    with pytest.raises(InvalidLevelError, match="Valid names: DEBUG, INFO, WARNING, ERROR, CRITICAL"):
        normalize_level_name(given)


def test_custom_level_names_are_accepted():
    """A name registered with logging.addLevelName resolves like a built-in one."""

    logging.addLevelName(25, "NOTICE")

    assert normalize_level_name("notice") == 25


def test_every_entry_point_validates():
    """with_level and with_subscriber(level=) both raise on a bad level."""

    with pytest.raises(InvalidLevelError):
        lab().with_level("DEBG")
    with pytest.raises(InvalidLevelError):
        lab().with_subscriber(print, level="LOUD")


@pytest.mark.parametrize(("build", "expected"), [
    (lambda: lab().with_experiment("standard"), logging.INFO),
    (lambda: lab().with_profile("investigator"), logging.INFO),
    (lambda: lab().with_profile("observer"), logging.WARNING),
    (lambda: lab().with_experiment("minimalist"), logging.WARNING),
    (lambda: lab().with_experiment("minimalist").with_experiment("FILE"), logging.WARNING),
    (lambda: lab().with_profile("observer").with_level("DEBUG"), logging.DEBUG),
], ids=["standard", "investigator", "observer", "minimalist", "minimalist+file", "explicit wins"])
def test_default_level_rule(build, expected):
    """CR-7: INFO unless minimalist is in the logger (WARNING); with_level() always wins."""

    assert build().build("levels.default").level == expected


def test_default_level_is_one_rule():
    """The rule itself, on a plan."""

    assert default_level([ExperimentType.STANDARD]) == logging.INFO
    assert default_level([ExperimentType.MINIMALIST, ExperimentType.FILE]) == logging.WARNING


def test_profile_functions_share_the_defaults():
    """Called directly, profiles default to INFO, and observer to WARNING."""

    from logger_lab.profiles import investigator, observer

    assert investigator("levels.direct.inv").level == logging.INFO
    assert observer("levels.direct.obs").level == logging.WARNING


def test_log_dir_that_is_a_file_raises_log_directory_error():
    """TS-2: get_log_dir wraps the OSError when the path exists but isn't a directory."""

    Path("not_a_dir").write_text("I'm a file", encoding="utf-8")

    with pytest.raises(LogDirectoryError, match="not_a_dir") as err:
        get_log_dir("not_a_dir/logs")

    assert isinstance(err.value.__cause__, OSError)


def test_build_profile_is_public():
    """PF-2: custom profiles use logger_lab.profiles.build_profile."""

    from logger_lab.experiments import minimalist_experiment
    from logger_lab.profiles import build_profile

    logger = build_profile("levels.custom", logging.ERROR, minimalist_experiment)

    assert logger.level == logging.ERROR and len(logger.handlers) == 1
