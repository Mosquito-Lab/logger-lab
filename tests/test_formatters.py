"""The JSON record schema (Mosquito Lab Logging Standard v1.2), the text layouts, and `log_event()`."""

import inspect
import json
import logging
import sys
from datetime import datetime

from logger_lab import drain, lab, log_event
from logger_lab.logging_kernel import DATE_FORMAT, TEXT_LAYOUTS, JSONFormatter, text_formatter


class ListHandler(logging.Handler):
    """Collects formatted records in memory."""

    def __init__(self) -> None:
        """Start with no records."""

        super().__init__()
        self.lines: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        """Store the formatted record."""

        self.lines.append(self.format(record))


def json_logger(name: str) -> tuple[logging.Logger, ListHandler]:
    """Return a logger whose only handler captures `JSONFormatter` output."""

    handler = ListHandler()
    handler.setFormatter(JSONFormatter())
    logger = logging.getLogger(name)
    logger.handlers = [handler]
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    return logger, handler


def test_plain_record_has_the_v1_2_fields_and_the_text_timestamp():
    """timestamp, level, logger, message and source; nothing else. The timestamp is exactly the text format's."""

    logger, handler = json_logger("json.plain")
    logger.info("hello %s", "world")

    entry = json.loads(handler.lines[0])
    record = logging.LogRecord("x", logging.INFO, __file__, 1, "m", (), None)

    assert set(entry) == {"timestamp", "level", "logger", "message", "source"}
    assert entry["level"] == "INFO" and entry["message"] == "hello world" and entry["logger"] == "json.plain"
    assert set(entry["source"]) == {"module", "function", "line"}
    assert datetime.strptime(entry["timestamp"], DATE_FORMAT)
    assert json.loads(JSONFormatter().format(record))["timestamp"] == text_formatter().formatTime(record, DATE_FORMAT)


def test_exceptions_are_serialized():
    """KN-17: logger.exception() puts type, message and the full traceback under "exception"."""

    logger, handler = json_logger("json.exc")

    try:
        raise ValueError("bad token")
    except ValueError:
        logger.exception("login failed")

    exception = json.loads(handler.lines[0])["exception"]

    assert exception["type"] == "ValueError" and exception["message"] == "bad token"
    assert exception["traceback"].startswith("Traceback (most recent call last)")
    assert "ValueError: bad token" in exception["traceback"]


def test_stack_info_is_serialized():
    """stack_info=True adds a "stack" field."""

    logger, handler = json_logger("json.stack")
    logger.warning("where was I called from", stack_info=True)

    assert json.loads(handler.lines[0])["stack"].startswith("Stack (most recent call last)")


def test_exception_reaches_json_through_async(capsys):
    """End to end with ai_agent + ASYNC: the traceback survives the queue and lands in the JSON on stderr."""

    logger = lab().with_profile("ai_agent").with_catalyst("ASYNC").build("json.async")

    try:
        raise KeyError("missing")
    except KeyError:
        logger.exception("lookup failed")

    assert drain(5)
    entry = json.loads(capsys.readouterr().err.strip().splitlines()[-1])

    assert entry["logger"] == "json.async" and entry["exception"]["type"] == "KeyError"


def test_log_event_fills_extra():
    """`log_event()` puts event, context and tags under ``extra``."""

    logger, handler = json_logger("json.event")
    log_event(logger, logging.WARNING, "login", event="user_login", context={"user_id": 42}, tags=["auth"])

    entry = json.loads(handler.lines[0])

    assert entry["extra"] == {"event": "user_login", "context": {"user_id": 42}, "tags": ["auth"]}


def test_log_event_source_is_the_caller():
    """KN-10: ``source`` points at the line that called `log_event()`, not at the helper."""

    logger, handler = json_logger("json.source")
    line = inspect.currentframe().f_lineno + 1  # pyrefly: ignore[missing-attribute]
    log_event(logger, logging.INFO, "where am I", event="probe")

    source = json.loads(handler.lines[0])["source"]

    assert source == {"module": "test_formatters", "function": "test_log_event_source_is_the_caller", "line": line}


def test_unserializable_values_fall_back_to_str():
    """Non-JSON values are stringified instead of crashing the handler."""

    logger, handler = json_logger("json.obj")
    log_event(logger, logging.INFO, "obj", event="obj", context={"value": object()})

    assert "object object at" in json.loads(handler.lines[0])["extra"]["context"]["value"]


def test_text_layouts_by_detail():
    """minimal: level + message; standard: time, name, level, message; verbose: adds module.function:line."""

    record = logging.LogRecord("app", logging.INFO, "/src/app/jobs.py", 42, "done", (), None, func="run")

    assert text_formatter("minimal").format(record) == "INFO: done"
    assert text_formatter("standard").format(record).endswith(" - app - INFO - done")
    assert text_formatter("verbose").format(record).endswith(" - app - INFO - jobs.run:42 - done")
    assert text_formatter().format(record) == text_formatter("standard").format(record)
    assert set(TEXT_LAYOUTS) == {"minimal", "standard", "verbose"}


def test_a_traceback_is_rendered_once_however_many_formatters_see_it():
    """KN-46: like logging.Formatter, the JSON format caches the traceback in record.exc_text."""

    renders: list[int] = []

    class CountingJSON(JSONFormatter):
        """Counts how often it renders a traceback."""

        def formatException(self, ei) -> str:
            """Render as usual, and count it."""

            renders.append(1)

            return super().formatException(ei)

    try:
        raise ValueError("once")
    except ValueError:
        record = logging.LogRecord("x", logging.ERROR, __file__, 1, "failed", (), sys.exc_info())

    first, second = CountingJSON().format(record), CountingJSON().format(record)

    assert len(renders) == 1
    assert json.loads(first)["exception"]["traceback"] == json.loads(second)["exception"]["traceback"]
