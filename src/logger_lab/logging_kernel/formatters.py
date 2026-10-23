"""
Formatters and the structured-event helper.

* `JSONFormatter`: the **Mosquito Lab Logging Standard v1.2** (the ``JSON`` format).
* `text_formatter`: the plain-text layouts (``TEXT`` format), one per detail level.
* `log_event`: log a structured event without building ``extra=`` by hand.

Both formats write timestamps the same way, with `DATE_FORMAT` in local time. Formatters
hold no state between records, so they are safe on any thread.
"""

import json
import logging
from datetime import datetime
from typing import Any

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"  # Every timestamp, text and JSON alike: local time, to the second


###########################
# Structured event helper #
###########################

def log_event(logger: logging.Logger, level: int, msg: str, *, event: str,
              context: dict[str, Any] | None = None, tags: list[str] | None = None) -> None:
    """
    Log a structured record without making callers build ``extra=``.

    It builds a fresh ``extra`` dict on every call, so successive records never share
    mutable state. The record's source (module, function, line) is the caller of
    `log_event`, not this helper.

    Args:
        logger:  The logger to log on.
        level:   A `logging` level constant, e.g. ``logging.INFO``.
        msg:     The human-readable message.
        event:   A machine-readable event name, e.g. ``"user_login"``.
        context: Any key/value payload for the event.
        tags:    Labels for filtering and search.
    Example::
        log_event(logger, logging.INFO, "User logged in", event="user_login",
                  context={"user_id": 42}, tags=["auth"])
    """

    extra = {
        "event": event,
        "context": context if context is not None else {},
        "tags": tags if tags is not None else [],
    }

    logger.log(level, msg, extra=extra, stacklevel=2)  # stacklevel=2: the record's source is our caller


###################
# The JSON format #
###################

class JSONFormatter(logging.Formatter):
    """
    Serialize every record as one JSON object, per the **Mosquito Lab Logging Standard v1.2**::

        {
            "timestamp": "2026-05-05 12:00:00",
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
    ``exc_info=True``). ``stack`` appears only with ``stack_info=True``, and ``extra`` only
    when fields were passed with ``extra=``. v1.1 added ``logger``, ``exception`` and
    ``stack`` to v1. v1.2 writes ``timestamp`` like the text format: `DATE_FORMAT`, local
    time (v1.1 used UTC ISO-8601 with microseconds).

    Standard `logging.LogRecord` attributes are left out of ``extra``. A value JSON can't
    hold is written with `str`.
    """

    # The attributes every LogRecord has, read from a real one, plus "message", which
    # Formatter.format adds. Anything else on a record is an extra.
    STANDARD_ATTRS = frozenset(
        logging.LogRecord(name="", level=0, pathname="", lineno=0, msg="", args=(), exc_info=None).__dict__
    ) | {"message"}

    def format(self, record: logging.LogRecord) -> str:
        """
        Serialize *record* to a single-line JSON string.

        The traceback is rendered once and cached in ``record.exc_text``, as
        `logging.Formatter` does, so several formatters on one record don't render it again.
        """

        entry: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created).strftime(DATE_FORMAT),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "source": {"module": record.module, "function": record.funcName, "line": record.lineno},
        }

        if record.exc_info and record.exc_info[0] is not None:
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)

            exc_type, exc_value, _ = record.exc_info
            entry["exception"] = {"type": exc_type.__name__, "message": str(exc_value), "traceback": record.exc_text}

        if record.stack_info:
            entry["stack"] = self.formatStack(record.stack_info)

        extras = {key: value for key, value in record.__dict__.items() if key not in self.STANDARD_ATTRS}

        if extras:
            entry["extra"] = extras

        return json.dumps(entry, default=str)


###################
# The TEXT format #
###################

TEXT_LAYOUTS = {  # The TEXT format's layout for each detail level
    "minimal":  "%(levelname)s: %(message)s",
    "standard": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "verbose":  "%(asctime)s - %(name)s - %(levelname)s - %(module)s.%(funcName)s:%(lineno)d - %(message)s",
}


def text_formatter(detail: str = "standard") -> logging.Formatter:
    """
    Return the plain-text `logging.Formatter` for a detail level (the ``TEXT`` format).

    Layouts::
        minimal   INFO: Saved
        standard  2026-05-05 10:00:00 - my_app - INFO - Saved
        verbose   2026-05-05 10:00:00 - my_app - INFO - store.save:42 - Saved

    Args:
        detail: ``"minimal"``, ``"standard"`` or ``"verbose"`` (from the detail features).
    Returns:
        A configured `logging.Formatter`.
    """

    return logging.Formatter(fmt=TEXT_LAYOUTS[detail], datefmt=DATE_FORMAT)
