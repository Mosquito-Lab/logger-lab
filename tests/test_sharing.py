"""CR-9: one handler per log file, shared across loggers, with per-module levels and compositions."""

import logging
from pathlib import Path

import pytest

from logger_lab import LogFileClashError, SharedFileSettingsWarning, lab
from logger_lab.logging_kernel import LAB_HANDLERS, SHARED_FILES, clear_handlers, file_key

from helpers import file_handler


def test_modules_on_one_file_share_one_handler():
    """Two module loggers writing to ``app.log`` get the very same handler object."""

    a = lab().with_profile("investigator").build("app.module_a")
    b = lab().with_profile("investigator").build("app.module_b")

    assert file_handler(a) is file_handler(b)
    assert list(SHARED_FILES.values())[0].owners == {"app.module_a": 1, "app.module_b": 1}


def test_each_module_keeps_its_own_level():
    """The shared handler has no level; each logger's level filters its own records."""

    chatty = lab().with_output("file").with_level("DEBUG").build("app.chatty")
    quiet = lab().with_output("file").with_level("WARNING").build("app.quiet")

    assert file_handler(chatty).level == logging.NOTSET

    chatty.debug("chatty debug")
    quiet.debug("quiet debug")
    quiet.warning("quiet warning")

    text = Path("logs/app.log").read_text(encoding="utf-8")

    assert "chatty debug" in text and "quiet warning" in text
    assert "quiet debug" not in text


def test_each_module_picks_its_own_composition():
    """Modules compose differently and still share the file they have in common."""

    bots = lab().with_profile("conspiracy_theorist").build("app.bots")  # verbose console + verbose rotating file
    loaders = (
        lab().with_profile("ai_agent").with_output("file").with_feature("VERBOSE", on="file").with_feature("ROTATING")
        .build("app.loaders")
    )

    assert file_handler(bots) is file_handler(loaders)
    assert len(bots.handlers) == 2 and len(loaders.handlers) == 2


@pytest.mark.parametrize(("second", "wanted", "held"), [
    (lambda: lab().with_output("file").with_feature("ROTATING"), r"FILE\[TEXT\]\+ROTATING", r"FILE\[TEXT\]"),
    (lambda: lab().with_output("file").with_format("JSON"), r"FILE\[JSON\]", r"FILE\[TEXT\]"),
], ids=["plain vs rotating", "text vs JSON"])
def test_a_different_setup_on_an_open_file_raises_and_leaves_nothing_half_built(second, wanted, held):
    """One handler can't be both plain and rotating, or both text and JSON. The error names both loggers and the fix."""

    lab().with_output("file").build("app.loaders")

    clash = f"'app.bots' asked for .* as {wanted}, but it is already open as {held} for 'app.loaders'"

    with pytest.raises(LogFileClashError, match=clash) as err:
        second().build("app.bots")

    assert "with_output('file', filename=...)" in str(err.value)
    assert not [h for h in logging.getLogger("app.bots").handlers if h in LAB_HANDLERS]
    assert list(SHARED_FILES.values())[0].owners == {"app.loaders": 1}


def test_handlers_logger_lab_did_not_create_are_detached_not_closed():
    """A rebuild never closes someone else's handler, because it may serve other loggers."""

    logger = lab().with_output("console").build("app.mixed")
    theirs = logging.FileHandler("theirs.log")  # a user's own handler, outside logger-lab
    logger.addHandler(theirs)

    lab().with_output("console").build("app.mixed")

    assert theirs not in logger.handlers and theirs.stream is not None
    theirs.close()


def test_different_settings_keep_the_first_and_warn():
    """A second logger with another size or detail joins the open file, which keeps its first settings."""

    first = lab().with_output("file").with_feature("ROTATING", max_bytes=5_000).build("app.first")

    ignored = r"'app.second' joined .* \(max_bytes=5000\); ignoring max_bytes=1000"

    with pytest.warns(SharedFileSettingsWarning, match=ignored):
        second = lab().with_output("file").with_feature("ROTATING", max_bytes=1_000).build("app.second")

    shared = file_handler(second)

    assert shared is file_handler(first)
    assert shared.size is not None and shared.size.max_bytes == 5_000

    with pytest.warns(SharedFileSettingsWarning, match="detail='standard'.*ignoring detail='minimal'"):
        lab().with_output("file").with_feature("ROTATING", max_bytes=5_000).with_feature("MINIMAL").build("app.third")


def test_sole_user_can_rebuild_its_file_differently():
    """A logger alone on its file may switch features or settings. That's a rebuild, not a clash."""

    old = file_handler(lab().with_output("file").build("app.solo"))
    new = file_handler(lab().with_output("file").with_feature("ROTATING").build("app.solo"))

    assert new is not old and old.stream is None
    assert SHARED_FILES[file_key("logs/app.log")].kind == "FILE[TEXT]+ROTATING"


def test_a_file_shares_by_its_whole_setup():
    """EX-13: the kind names the format and both rotations, and the settings hold every rule's values."""

    (lab().with_output("file").with_format("JSON").with_feature("ROTATING", max_bytes=5_000)
     .with_feature("TIMED", unit="hours").build("app.both"))
    shared = SHARED_FILES[file_key("logs/app.log")]

    assert shared.kind == "FILE[JSON]+ROTATING+TIMED"
    assert shared.settings == {"encoding": "utf-8", "backup_count": 3, "detail": "standard", "max_bytes": 5_000,
                               "every": 1, "unit": "hour", "day": None, "at": None, "utc": False}

    with pytest.warns(SharedFileSettingsWarning, match="unit='hour'.*ignoring unit='day'"):
        (lab().with_output("file").with_format("JSON").with_feature("ROTATING", max_bytes=5_000)
         .with_feature("TIMED").build("app.daily"))


def test_file_closes_only_when_its_last_logger_lets_go():
    """Releasing one of two users keeps the file open; releasing the last closes it."""

    a = lab().with_output("file").build("app.a")
    b = lab().with_output("file").build("app.b")
    handler = file_handler(a)

    clear_handlers(a)
    assert handler.stream is not None

    b.info("still writing")
    clear_handlers(b)

    assert handler.stream is None
    assert SHARED_FILES == {}


def test_closed_handler_never_reopens_its_file():
    """A record arriving after release is dropped instead of reopening the file (stdlib would reopen)."""

    logger = lab().with_output("file").build("app.late")
    handler = file_handler(logger)
    record = logger.makeRecord("app.late", logging.INFO, __file__, 1, "late record", (), None)

    clear_handlers(logger)
    handler.handle(record)

    assert handler.stream is None
    assert "late record" not in Path("logs/app.log").read_text(encoding="utf-8")
