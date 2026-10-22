"""
Formatters and the structured-event helper.

* `JSONFormatter` — the **Mosquito Lab Logging Standard v1.1** (used by the ``ai`` experiment).
* `build_file_formatter` — the line format both file experiments write.
* `log_event` — log a structured event without building ``extra=`` by hand.

Formatters hold no state between records, so they are safe on any thread.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any


# Structured event helper
def log_event(
        logger: logging.Logger, level: int,
        msg: str, *, event: str,
        context: dict[str, Any] | None = None,
        tags: list[str] | None = None,
) -> None:
    """
    Fire a structured log record without exposing ``extra=`` to callers.

    Constructs a fresh ``extra`` dict on every call so successive log
    statements never share mutable state.  The record's source (module,
    function, line) is the caller of `log_event`, not this helper.

    Args:
        logger:  The logger to emit on.
        level:   Standard `logging` level constant, e.g. ``logging.INFO``.
        msg:     Human-readable log message.
        event:   Machine-readable event identifier, e.g. ``"user_login"``.
        context: Arbitrary key/value payload attached to the event.
        tags:    Optional list of string labels for filtering/search.
    Example::
        log_event(
            logger, logging.INFO, "User logged in",
            event="user_login",
            context={"user_id": 42},
            tags=["auth"]
        )
    """

    logger.log(
        level,
        msg,
        extra={
            "event": event,
            "context": context if context is not None else {},
            "tags": tags if tags is not None else [],
        },
        stacklevel=2,  # attribute the record to our caller, not to log_event itself
    )


# JSONFormatter
class JSONFormatter(logging.Formatter):
    """
    Structured formatter that serializes every record as a JSON object.
    Conforms to the **Mosquito Lab Logging Standard v1.1**:

    {
        "timestamp": "2026-05-05T10:00:00+00:00",
        "level":     "ERROR",
        "logger":    "app.auth",
        "message":   "Login failed",
        "source": {
            "module":   "auth",
            "function": "login",
            "line":     88
        },
        "exception": {
            "type":      "ValueError",
            "message":   "bad token",
            "traceback": "Traceback (most recent call last): ..."
        },
        "stack": "Stack (most recent call last): ...",
        "extra": {
            "event":   "user_login",
            "context": {"user_id": 42},
            "tags":    ["auth"]
        }
    }

    ``exception`` appears only when the record carries one (``logger.exception()``,
    ``exc_info=True``), ``stack`` only with ``stack_info=True``, and ``extra`` only when
    fields were injected via ``extra=``.  v1.1 adds ``logger``, ``exception`` and
    ``stack`` to v1; every v1 field is unchanged.

    Standard `logging.LogRecord` attributes are filtered out of ``extra`` so they don't
    pollute it.  Non-serializable values fall back to `str` via json.dumps() ``default=str``.
    """

    # Built once from a real LogRecord, so every attribute the stdlib adds is excluded from "extra".
    STANDARD_ATTRS = frozenset(
        logging.LogRecord(
            name="", level=0, pathname="", lineno=0,
            msg="", args=(), exc_info=None,
        ).__dict__.keys()
    ) | {"message"}  # "message" is synthesized by Formatter.format — exclude it too

    # **Mosquito Lab Logging Standard v1.1**
    def format(self, record: logging.LogRecord) -> str:
        """
        Serialize *record* to a JSON string.

        Args:
            record: The log record emitted by a `logging.Logger`.
        Returns:
            A single-line JSON string.
        """

        # A log entry
        entry: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "source": {
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
            },
        }

        if record.exc_info and record.exc_info[0] is not None:
            exc_type, exc_value, _ = record.exc_info
            entry["exception"] = {
                "type": exc_type.__name__,
                "message": str(exc_value),
                "traceback": self.formatException(record.exc_info),
            }

        if record.stack_info:
            entry["stack"] = self.formatStack(record.stack_info)

        # Any extra content not caught in STANDARD_ATTRS
        extras = {
            k: v for k, v in record.__dict__.items() if k not in self.STANDARD_ATTRS
        }

        # Adds the extras to the entry
        if extras:
            entry["extra"] = extras

        return json.dumps(entry, default=str)


# Schema for the file formatter
def build_file_formatter() -> logging.Formatter:
    """
    Return a `logging.Formatter` suitable for persistent log files.

    Format::
        2026-05-05 10:00:00 - my_app - INFO - login:42 - User logged in
    Returns:
        A configured `logging.Formatter` instance.
    """

    return logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
