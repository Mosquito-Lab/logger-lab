"""
Verbose experiment — full-context plain-text console handler.

Emits every available field on a single line: timestamp, logger name,
level, module, function, line number, and message.  Useful when you
need maximum context without the overhead of writing to disk.

Used by the ``conspiracy_theorist`` profile.
"""

from logging import DEBUG, Handler, Formatter, StreamHandler

from logger_lab.logging_kernel.handlers import configure_handler

#: Format string used by the verbose handler.
_VERBOSE_FMT = (
    "%(asctime)s | %(name)-20s | %(levelname)-8s | "
    "%(module)s.%(funcName)s:%(lineno)d | %(message)s"
)

#: Date format — ISO-8601 date/time, no timezone suffix (local time).
_DATE_FMT = "%Y-%m-%d %H:%M:%S"


# noinspection PyUnusedLocal
def verbose_experiment(level: int = DEBUG, **kwargs: object) -> list[Handler]:
    """
    Return a plain `~logging.StreamHandler` with full-context formatting.

    The format exposes every standard `~logging.LogRecord` field
    in a single line, making it easy to grep for module, function, or
    line-number information without opening a file.

    Args:
        level:    Logging level for the handler.
                  Defaults to :data:`logging.DEBUG`.
        **kwargs: Reserved for future extension.
    Returns:
        A single-element list containing the configured `~logging.StreamHandler`.
    Example::
        handlers = verbose_experiment(logging.DEBUG)
        for h in handlers:
            logger.addHandler(h)
    """

    formatter = Formatter(fmt=_VERBOSE_FMT, datefmt=_DATE_FMT)
    handler = StreamHandler()

    return [configure_handler(handler, level, formatter)]
