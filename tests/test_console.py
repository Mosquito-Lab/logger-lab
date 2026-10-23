"""The console output: one Rich console, its stream, its formats, the detail features, and never raising."""

import json
import re

import pytest

from logger_lab import lab
from logger_lab.outputs import LabRichHandler

TIME = re.compile(r"\d{2}:\d{2}:\d{2}")  # A clock time, as both Rich and TEXT print it


def test_rich_on_stderr_by_default_and_stdout_for_every_format(capsys):
    """Default format RICH on stderr, which keeps stdout free. stream="stdout" moves every format."""

    logger = lab().with_output("console").build("console.default")
    logger.info("hello rich")
    out, err = capsys.readouterr()

    assert isinstance(logger.handlers[0], LabRichHandler)
    assert "hello rich" in err and out == ""

    for format_ in ("RICH", "TEXT", "JSON"):
        logger = lab().with_output("console", stream="stdout").with_format(format_).build(f"console.out.{format_}")
        logger.info("to stdout")
        out, err = capsys.readouterr()

        assert "to stdout" in out and err == "", format_


@pytest.mark.parametrize(("feature", "pattern"), [
    (None, r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} - console\.text - INFO - plain line$"),
    ("MINIMAL", r"^INFO: plain line$"),
    ("VERBOSE", r"^\S+ \S+ - console\.text - INFO - test_console\.test_text_detail:\d+ - plain line$"),
], ids=["standard", "minimal", "verbose"])
def test_text_detail(capsys, feature, pattern):
    """TEXT: time, name, level and message by default. MINIMAL keeps level and message. VERBOSE adds where."""

    builder = lab().with_output("console").with_format("TEXT")
    (builder.with_feature(feature) if feature else builder).build("console.text").info("plain line")

    assert re.match(pattern, capsys.readouterr().err.strip())


@pytest.mark.parametrize(("feature", "time", "where"), [
    (None, True, False), ("MINIMAL", False, False), ("VERBOSE", True, True),
], ids=["standard", "minimal", "verbose"])
def test_rich_detail(capsys, feature, time, where):
    """RICH shows the same three details as columns. VERBOSE also names the logger and the source file."""

    builder = lab().with_output("console")
    (builder.with_feature(feature) if feature else builder).build("console.rich").warning("rich line")
    err = capsys.readouterr().err

    assert "WARNING" in err and "rich line" in err
    assert bool(TIME.search(err)) is time
    assert ("console.rich: rich line" in err and "test_console.py" in err) is where


def test_json_console_is_one_object_per_line(capsys):
    """ai_agent: every record is one parseable JSON object on stderr."""

    logger = lab().with_profile("ai_agent").build("console.json")
    logger.info("first")
    logger.warning("second")

    assert [json.loads(line)["message"] for line in capsys.readouterr().err.strip().splitlines()] == ["first", "second"]


def test_brackets_in_a_message_are_text_not_markup(capsys):
    """EX-8: with markup on, "[/usr/bin]" raised MarkupError out of logger.info() and crashed the caller."""

    lab().with_output("console").build("console.markup").info("scanning [/usr/bin] and [red]")
    err = capsys.readouterr().err

    assert "Logging error" not in err  # printed, not caught as an error
    assert "[/usr/bin]" in err and "[red]" in err


def test_a_bad_format_call_is_reported_not_raised(capsys):
    """EX-8: RichHandler formats outside its own try. LabRichHandler reports the error like every stdlib handler."""

    lab().with_output("console").build("console.badformat").info("%d", "not a number")

    assert "Logging error" in capsys.readouterr().err


def test_markup_can_still_be_asked_for_per_record(capsys):
    """extra={"markup": True} styles one record, and the tag itself is not printed."""

    lab().with_output("console").build("console.styled").info("[bold]loud[/bold]", extra={"markup": True})
    err = capsys.readouterr().err

    assert "loud" in err and "[bold]" not in err
