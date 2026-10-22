"""File args, handler closing, and rotation on a real filesystem (Windows included)."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

import pytest

from logger_lab import ExperimentType, ProfileType, lab
from logger_lab.logging_kernel import clear_handlers


def file_paths(logger: logging.Logger) -> list[str]:
    """Return the resolved paths of *logger*'s file handlers, in order."""

    return [h.baseFilename for h in logger.handlers if isinstance(h, logging.FileHandler)]


def test_defaults_write_to_logs_app_log():
    """No file args → each file experiment uses ``logs/app.log``."""

    logger = lab().with_experiment("FILE").build("defaults")

    assert file_paths(logger) == [str(Path("logs/app.log").resolve())]


@pytest.mark.parametrize("experiment", list(ExperimentType))
def test_every_experiment_accepts_file_args(experiment):
    """Console experiments ignore file args; file experiments honour them."""

    logger = lab().with_experiment(experiment).with_file_args("out", filename="run.log").build(f"fa.{experiment.value}")

    assert all(p == str(Path("out/run.log").resolve()) for p in file_paths(logger))


@pytest.mark.parametrize("profile", list(ProfileType))
def test_every_profile_forwards_file_args(profile):
    """The profile's file experiments receive the builder's file args."""

    logger = lab().with_profile(profile).with_file_args(f"out_{profile.value}").build(f"fp.{profile.value}")

    assert all(Path(p).parent == Path(f"out_{profile.value}").resolve() for p in file_paths(logger))


def test_rotating_file_receives_all_five_args():
    """``max_bytes``, ``backup_count`` and ``encoding`` reach the `RotatingFileHandler`."""

    logger = lab().with_experiment("ROTATING").with_file_args("rot", "r.log", "utf-16", 1234, 7).build("rot")
    handler = logger.handlers[0]

    assert isinstance(handler, RotatingFileHandler)
    assert (handler.maxBytes, handler.backupCount, handler.encoding) == (1234, 7, "utf-16")


def test_clear_handlers_closes_what_it_removes():
    """Step 2: a detached file handler is closed, not left holding its file."""

    logger = lab().with_experiment("FILE").build("closing")
    handler = logger.handlers[0]

    clear_handlers(logger)

    assert logger.handlers == []
    assert isinstance(handler, logging.FileHandler)
    assert handler.stream is None  # FileHandler.close() drops its stream


def test_rebuilding_a_logger_on_the_same_file_keeps_it_open():
    """Rebuilding a name with the same file experiment shares the open handler — no reopen."""

    first = lab().with_experiment("FILE").build("rebuild").handlers[0]
    second = lab().with_experiment("FILE").build("rebuild").handlers[0]

    assert second is first
    assert isinstance(first, logging.FileHandler) and first.stream is not None


def test_rebuilding_a_logger_onto_another_file_closes_the_old_one():
    """Moving a logger to a different file releases — and, as its last user, closes — the old file."""

    old = lab().with_experiment("FILE").build("move").handlers[0]
    lab().with_experiment("FILE").with_file_args("elsewhere").build("move")

    assert isinstance(old, logging.FileHandler)
    assert old.stream is None


def test_conspiracy_theorist_rotates(capsys):
    """The profile that used to fail with WinError 32 now rolls over cleanly."""

    logger = lab().with_profile("conspiracy_theorist").with_file_args("ct", max_bytes=200).build("ct_rotate")

    for i in range(10):
        logger.info("record %d with enough padding to force a rollover", i)

    assert Path("ct/app.log.1").exists()
    assert "PermissionError" not in capsys.readouterr().err
