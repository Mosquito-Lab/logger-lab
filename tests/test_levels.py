"""Levels: what's accepted, what raises, and the one default, INFO, for every logger."""

import logging
from pathlib import Path

import pytest

from logger_lab import InvalidLevelError, ProfileType, lab
from logger_lab.logging_kernel import clear_handlers, normalize_level_name


# noinspection PyProtectedMember
def test_accepted_levels(monkeypatch):
    """Names in any case, the stdlib aliases, custom names, and any integer 0 or above."""

    # addLevelName() writes to logging's two level tables. Copies stand in for them, so the
    # custom name is gone when the test ends and no later test sees it (TS-8).
    monkeypatch.setattr(logging, "_levelToName", dict(logging._levelToName))
    monkeypatch.setattr(logging, "_nameToLevel", dict(logging._nameToLevel))
    logging.addLevelName(25, "NOTICE")

    for given, expected in [("debug", logging.DEBUG), ("WARN", logging.WARNING), ("fatal", logging.CRITICAL),
                            ("notice", 25), (logging.ERROR, logging.ERROR), (0, 0), (25, 25)]:
        assert normalize_level_name(given) == expected


@pytest.mark.parametrize("given", ["DEBG", "", "10", -1, 2.5, True, None])
def test_rejected_levels_raise_and_list_the_valid_names(given):
    """KN-2: no silent fallback to INFO. A typo, a numeric string, a negative number or a wrong type raises."""

    with pytest.raises(InvalidLevelError, match="Valid names: DEBUG, INFO, WARNING, ERROR, CRITICAL"):
        normalize_level_name(given)


def test_every_entry_point_validates():
    """with_level() and with_subscriber(level=) both raise on a bad level."""

    with pytest.raises(InvalidLevelError):
        lab().with_level("DEBG")
    with pytest.raises(InvalidLevelError):
        lab().with_subscriber(print, level="LOUD")


def test_every_logger_defaults_to_info_and_with_level_wins():
    """One default for every profile and every hand composition. Quieter or louder is a with_level() away."""

    for profile in ProfileType:
        logger = lab().with_profile(profile).build(f"levels.{profile.value}")

        assert logger.level == logging.INFO
        clear_handlers(logger)  # The next profile's file may be set up differently

    hand = lab().with_output("file", filename="hand.log").with_feature("TIMED").build("levels.hand")

    assert hand.level == logging.INFO
    assert lab().with_profile("observer").with_level("WARNING").build("levels.quiet").level == logging.WARNING


def test_handlers_have_no_level_so_the_logger_level_is_the_one_switch(capsys):
    """Console and file are NOTSET, so a setLevel() after the build reaches both (EX-9: the console kept INFO)."""

    logger = lab().with_profile("investigator").with_format("TEXT", on="console").build("levels.switch")

    assert [h.level for h in logger.handlers] == [logging.NOTSET, logging.NOTSET]

    logger.setLevel(logging.DEBUG)
    logger.debug("debug after the build")

    assert "debug after the build" in capsys.readouterr().err
    assert "debug after the build" in Path("logs/app.log").read_text(encoding="utf-8")
