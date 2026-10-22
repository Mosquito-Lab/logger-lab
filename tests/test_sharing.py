"""CR-9: one handler per log file, shared across loggers, with per-module levels and experiments."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

import pytest

from logger_lab import LogFileClashError, SharedFileSettingsWarning, lab
from logger_lab.logging_kernel import LAB_HANDLERS, SHARED_FILES, clear_handlers, file_key


def file_handler(logger: logging.Logger) -> logging.FileHandler:
    """Return *logger*'s one file handler."""

    (handler,) = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]

    return handler


def test_modules_on_one_file_share_one_handler():
    """Two module loggers writing to ``app.log`` get the very same handler object."""

    a = lab().with_profile("investigator").build("app.module_a")
    b = lab().with_profile("investigator").build("app.module_b")

    assert file_handler(a) is file_handler(b)
    assert list(SHARED_FILES.values())[0].owners == {"app.module_a": 1, "app.module_b": 1}


def test_each_module_keeps_its_own_level():
    """The shared handler has no level; each logger's level filters its own records."""

    chatty = lab().with_experiment("FILE").with_level("DEBUG").build("app.chatty")
    quiet = lab().with_experiment("FILE").with_level("WARNING").build("app.quiet")

    assert file_handler(chatty).level == logging.NOTSET

    chatty.debug("chatty debug")
    quiet.debug("quiet debug")
    quiet.warning("quiet warning")

    text = Path("logs/app.log").read_text(encoding="utf-8")

    assert "chatty debug" in text and "quiet warning" in text
    assert "quiet debug" not in text


def test_each_module_picks_its_own_experiments():
    """Modules compose differently and still share the file they have in common."""

    bots = lab().with_profile("conspiracy_theorist").build("app.bots")          # verbose + rotating
    loaders = lab().with_experiment("ROTATING").with_experiment("AI").build("app.loaders")

    assert file_handler(bots) is file_handler(loaders)
    assert len(bots.handlers) == 2 and len(loaders.handlers) == 2


def test_different_experiment_on_an_open_file_raises():
    """``FILE`` and ``ROTATING`` can't share one handler — the error names both loggers and the fix."""

    lab().with_experiment("FILE").build("app.loaders")

    with pytest.raises(LogFileClashError, match=r"'app.bots' asked for .* as ROTATING, but it is already open as FILE for 'app.loaders'") as err:
        lab().with_experiment("ROTATING").build("app.bots")

    assert "with_file_args(filename=...)" in str(err.value)
    assert not [h for h in logging.getLogger("app.bots").handlers if h in LAB_HANDLERS]  # nothing half-built left
    assert list(SHARED_FILES.values())[0].owners == {"app.loaders": 1}


def test_handlers_logger_lab_did_not_create_are_detached_not_closed():
    """A rebuild never closes someone else's handler — it may serve other loggers."""

    logger = lab().with_experiment("minimalist").build("app.mixed")
    theirs = logging.FileHandler("theirs.log")  # a user's own handler, outside logger-lab
    logger.addHandler(theirs)

    lab().with_experiment("minimalist").build("app.mixed")

    assert theirs not in logger.handlers and theirs.stream is not None
    theirs.close()


def test_different_settings_keep_the_first_and_warn():
    """A second logger with other sizes joins the open file, which keeps its first settings."""

    first = lab().with_experiment("ROTATING").with_file_args(max_bytes=5_000).build("app.first")

    with pytest.warns(SharedFileSettingsWarning, match=r"'app.second' joined .* \(max_bytes=5000\); ignoring max_bytes=1000"):
        second = lab().with_experiment("ROTATING").with_file_args(max_bytes=1_000).build("app.second")

    shared = file_handler(second)

    assert shared is file_handler(first)
    assert isinstance(shared, RotatingFileHandler) and shared.maxBytes == 5_000


def test_sole_user_can_rebuild_its_file_differently():
    """A logger alone on its file may switch experiment or settings — that's a rebuild, not a clash."""

    old = file_handler(lab().with_experiment("FILE").build("app.solo"))
    new = file_handler(lab().with_experiment("ROTATING").build("app.solo"))

    assert new is not old and old.stream is None
    assert SHARED_FILES[file_key("logs/app.log")].kind == "ROTATING"


def test_file_closes_only_when_its_last_logger_lets_go():
    """Releasing one of two users keeps the file open; releasing the last closes it."""

    a = lab().with_experiment("FILE").build("app.a")
    b = lab().with_experiment("FILE").build("app.b")
    handler = file_handler(a)

    clear_handlers(a)
    assert handler.stream is not None

    b.info("still writing")
    clear_handlers(b)

    assert handler.stream is None
    assert SHARED_FILES == {}


def test_different_paths_are_not_shared():
    """Sharing is per path — different files get different handlers."""

    a = lab().with_experiment("FILE").with_file_args(filename="a.log").build("app.a")
    b = lab().with_experiment("FILE").with_file_args(filename="b.log").build("app.b")

    assert file_handler(a) is not file_handler(b)


def test_closed_handler_never_reopens_its_file():
    """A record arriving after release is dropped instead of reopening the file (stdlib would reopen)."""

    logger = lab().with_experiment("FILE").build("app.late")
    handler = file_handler(logger)
    record = logger.makeRecord("app.late", logging.INFO, __file__, 1, "late record", (), None)

    clear_handlers(logger)
    handler.handle(record)

    assert handler.stream is None
    assert "late record" not in Path("logs/app.log").read_text(encoding="utf-8")
