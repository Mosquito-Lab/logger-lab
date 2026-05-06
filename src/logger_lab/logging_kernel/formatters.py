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
    statements never share mutable state.

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
    )


# JSONFormatter
class JSONFormatter(logging.Formatter):
    """
    Structured formatter that serialises every record as a JSON object.
    Conforms to the **Mosquito Lab Logging Standard v1**:

    {
        "timestamp": "2026-05-05T10:00:00+00:00",
        "level":     "INFO",
        "message":   "User logged in",
        "source": {
            "module":   "auth",
            "function": "login",
            "line":     88
        },
        "extra": {
            "event":   "user_login",
            "context": {"user_id": 42},
            "tags":    ["auth"]
        }
    }

    Any fields injected via ``extra=`` on the log call are collected
    under the top-level ``"extra"`` key.  Standard `logging.LogRecord`
    attributes are filtered out so they do not pollute that namespace.

    Non-serializable values fall back to `str` via json.dumps() ``default=str``.
    """

    # Build the exclusion set once at class definition time using a real
    # LogRecord so we catch every attribute the stdlib adds automatically.
    _STANDARD_ATTRS = frozenset(
        logging.LogRecord(
            name="", level=0, pathname="", lineno=0,
            msg="", args=(), exc_info=None,
        ).__dict__.keys()
    ) | {"message"}  # "message" is synthesised by Formatter.format — exclude it too

    # **Mosquito Lab Logging Standard v1**
    def format(self, record: logging.LogRecord) -> str:
        """
        Serialise *record* to a JSON string.

        Args:
            record: The log record emitted by a `logging.Logger`.
        Returns:
            A single-line JSON string.
        """

        # A log entry
        entry = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "source": {
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
            },
        }

        # Any extra content not caught in the STANDARD_ATTRS
        extras = {
            k: v for k, v in record.__dict__.items() if k not in self._STANDARD_ATTRS
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


# Schema for the console formatter
def build_console_formatter() -> logging.Formatter:
    """
    Return a minimal `logging.Formatter` for plain console output.

    Outputs the message only; Rich handlers supply their own formatting
    so this is used by non-Rich console handlers (e.g. ``verbose``,
    ``minimalist``).

    Returns:
        A configured `logging.Formatter` instance.
    """

    return logging.Formatter(fmt="%(message)s", datefmt="[%X]")
