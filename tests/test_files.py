"""
The file output: its options, its formats, its directory, and closing.

Tested on a real filesystem, Windows included.
"""

import json
import logging
import re
from pathlib import Path

import pytest

from logger_lab import LogDirectoryError, lab
from logger_lab.logging_kernel import clear_handlers, get_log_dir

from helpers import file_handler


def test_defaults_write_a_plain_utf8_file_at_logs_app_log():
    """No options: ``logs/app.log``, utf-8, three backups, and no rollover rules."""

    handler = file_handler(lab().with_output("file").build("files.defaults"))

    assert handler.baseFilename == str(Path("logs/app.log").resolve())
    assert (handler.encoding, handler.size, handler.schedule, handler.backup_count) == ("utf-8", None, None, 3)


def test_options_reach_the_handler_on_every_profile_with_a_file():
    """log_dir and filename configure each profile's file. encoding, backup_count and max_bytes reach the handler."""

    for profile in ("investigator", "conspiracy_theorist", "gui"):
        logger = (
            lab().with_profile(profile).with_output("file", log_dir=f"out_{profile}", filename="run.log")
            .build(f"files.{profile}")
        )

        assert Path(file_handler(logger).baseFilename) == Path(f"out_{profile}/run.log").resolve()
        clear_handlers(logger)

    builder = lab().with_output("file", encoding="utf-16", backup_count=7).with_feature("ROTATING", max_bytes=1234)
    handler = file_handler(builder.build("files.opts"))

    assert handler.size is not None
    assert (handler.size.max_bytes, handler.backup_count, handler.encoding) == (1234, 7, "utf-16")


def test_the_detail_features_work_on_the_file():
    """The file uses the same text layouts as the console (all three are pinned in test_formatters)."""

    lab().with_output("file").with_feature("VERBOSE").build("files.text").info("on disk")

    where = r"test_files\.test_the_detail_features_work_on_the_file:\d+"
    line = Path("logs/app.log").read_text(encoding="utf-8").strip()

    assert re.match(rf"^\S+ \S+ - files\.text - INFO - {where} - on disk$", line)


def test_json_on_a_file_is_json_lines_and_can_rotate():
    """One JSON object per line, exceptions included. Format and rotation are independent."""

    logger = lab().with_output("file").with_format("JSON").build("files.json")
    logger.info("one")

    try:
        raise RuntimeError("two")
    except RuntimeError:
        logger.exception("failed")

    entries = [json.loads(line) for line in Path("logs/app.log").read_text(encoding="utf-8").splitlines()]

    assert [e["message"] for e in entries] == ["one", "failed"]
    assert entries[1]["exception"]["type"] == "RuntimeError"

    rotating = (
        lab().with_output("file", filename="rot.log").with_format("JSON").with_feature("ROTATING", max_bytes=300)
        .build("files.json_rot")
    )

    for n in range(10):
        rotating.info("record %d", n)

    assert Path("logs/rot.log.1").exists()

    for path in Path("logs").glob("rot.log*"):
        assert all(json.loads(line) for line in path.read_text(encoding="utf-8").splitlines())


def test_releasing_closes_the_file_and_rebuilding_reuses_or_moves_it():
    """clear_handlers() closes. Rebuilding onto the same file shares the open handler; onto another, closes the old."""

    handler = file_handler(lab().with_output("file").build("files.cycle"))

    assert file_handler(lab().with_output("file").build("files.cycle")) is handler and handler.stream is not None

    lab().with_output("file", log_dir="elsewhere").build("files.cycle")

    assert handler.stream is None

    moved = file_handler(logging.getLogger("files.cycle"))
    clear_handlers(logging.getLogger("files.cycle"))

    assert logging.getLogger("files.cycle").handlers == [] and moved.stream is None


def test_conspiracy_theorist_rotates_on_windows(capsys):
    """PF-1: the profile that used to fail with WinError 32 rolls over cleanly."""

    logger = (
        lab().with_profile("conspiracy_theorist").with_output("file", log_dir="ct")
        .with_feature("ROTATING", max_bytes=200).build("files.ct")
    )

    for i in range(10):
        logger.info("record %d with enough padding to force a rollover", i)

    assert Path("ct/app.log.1").exists()
    assert "PermissionError" not in capsys.readouterr().err


def test_a_log_dir_that_cannot_be_created_raises_log_directory_error():
    """TS-2: get_log_dir wraps the OSError, and the file output reports it on build."""

    Path("blocked").write_text("a file, not a folder", encoding="utf-8")

    with pytest.raises(LogDirectoryError, match="blocked") as err:
        get_log_dir("blocked/logs")

    assert isinstance(err.value.__cause__, OSError)

    with pytest.raises(LogDirectoryError):
        lab().with_profile("investigator").with_output("file", log_dir="blocked/logs").build("files.blocked")
