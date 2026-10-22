"""The JSON record schema (Mosquito Lab Logging Standard v1) and `log_event()`."""

import inspect
import json
import logging

from logger_lab import log_event
from logger_lab.logging_kernel import JSONFormatter


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


def test_plain_record_has_the_v1_1_fields():
    """timestamp, level, logger, message and source — and no exception/stack/extra when there are none."""

    logger, handler = json_logger("json.plain")
    logger.info("hello %s", "world")

    entry = json.loads(handler.lines[0])

    assert set(entry) == {"timestamp", "level", "logger", "message", "source"}
    assert entry["level"] == "INFO" and entry["message"] == "hello world" and entry["logger"] == "json.plain"
    assert set(entry["source"]) == {"module", "function", "line"}
    assert entry["timestamp"].endswith("+00:00")


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
    """End to end: ai + async — the traceback survives the queue and lands in the JSON on stderr."""

    from logger_lab import drain, lab

    logger = lab().with_experiment("AI").with_experiment("ASYNC").build("json.async")

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
