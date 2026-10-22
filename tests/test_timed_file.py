"""TIMED_FILE theory: time-based rotation, shared and clash-checked like the other file experiments."""

import logging
import time
from pathlib import Path

import pytest

from logger_lab import ExperimentClashError, LogFileClashError, lab
from logger_lab.logging_kernel import SharedTimedRotatingFileHandler


def timed_handler(logger: logging.Logger) -> SharedTimedRotatingFileHandler:
    """Return *logger*'s timed rotating handler."""

    (handler,) = logger.handlers
    assert isinstance(handler, SharedTimedRotatingFileHandler)

    return handler


def test_defaults_rotate_daily_at_midnight_keeping_three():
    """Default: one file a day, ``backup_count`` (3) days kept, local time."""

    handler = timed_handler(lab().with_theory("TIMED_FILE").build("app.timed"))

    assert (handler.when, handler.interval, handler.backupCount, handler.utc) == ("MIDNIGHT", 86_400, 3, False)
    assert handler.level == logging.NOTSET


def test_theory_options_and_file_args_reach_the_handler():
    """when/interval/utc come from with_theory(); log_dir/filename/backup_count from with_file_args()."""

    logger = (
        lab().with_theory("TIMED_FILE", when="H", interval=2, utc=True)
        .with_file_args("timed", filename="hourly.log", backup_count=24).build("app.timed")
    )
    handler = timed_handler(logger)

    assert (handler.when, handler.interval, handler.backupCount, handler.utc) == ("H", 7_200, 24, True)
    assert Path(handler.baseFilename) == Path("timed/hourly.log").resolve()


def test_rollover_writes_a_dated_backup(capsys):
    """Forcing the rollover time into the past rotates on the next record — no WinError 32."""

    logger = lab().with_theory("TIMED_FILE").build("app.timed")
    handler = timed_handler(logger)

    logger.info("yesterday")
    handler.rolloverAt = int(time.time()) - 1  # pretend midnight passed a second ago (not 0: Windows can't date 1969)
    logger.info("today")

    backups = list(Path("logs").glob("app.log.*"))

    assert len(backups) == 1 and "yesterday" in backups[0].read_text(encoding="utf-8")
    assert "today" in Path("logs/app.log").read_text(encoding="utf-8")
    assert "PermissionError" not in capsys.readouterr().err


def test_loggers_share_one_timed_handler():
    """Same path, same theory, same settings → one handler for both modules."""

    a = lab().with_theory("TIMED_FILE").build("app.a")
    b = lab().with_theory("TIMED_FILE").build("app.b")

    assert timed_handler(a) is timed_handler(b)


def test_clashes_with_other_file_experiments():
    """FILE channel in a logger; a different kind on an open path across loggers."""

    with pytest.raises(ExperimentClashError, match="FILE channel"):
        lab().with_experiment("ROTATING").with_theory("TIMED_FILE").build("app.both")

    lab().with_experiment("ROTATING").build("app.size")

    with pytest.raises(LogFileClashError, match="as TIMED_FILE, but it is already open as ROTATING"):
        lab().with_theory("TIMED_FILE").build("app.time")


def test_works_behind_async():
    """A theory is an output like any other, so ASYNC can dispatch to it."""

    from logger_lab import drain

    logger = lab().with_theory("TIMED_FILE").with_experiment("ASYNC").build("app.timed_async")
    logger.warning("queued for the timed file")

    assert drain(5)
    assert "queued for the timed file" in Path("logs/app.log").read_text(encoding="utf-8")
