"""
Timed-file theory — time-based log rotation (trial stage).

Rolls the log file over on a schedule instead of by size: by default once a day at
midnight, keeping *backup_count* days (``app.log``, ``app.log.2026-10-21``, …).  Built on
`logging.handlers.TimedRotatingFileHandler`, shared through `share_file_handler()` like the
other file experiments — one handler per file, safe rotation on Windows, thread-safe.
Writes to the FILE channel.

Select it with ``with_theory("TIMED_FILE", when="midnight", interval=1, utc=False, at_time=None)``;
``log_dir``, ``filename``, ``encoding`` and ``backup_count`` come from `with_file_args()`.
"""

from datetime import time
from logging import INFO, NOTSET, Handler
from pathlib import Path

from logger_lab.logging_kernel.constants import DEFAULT_BACKUP_COUNT, DEFAULT_ENCODING, DEFAULT_FILENAME, DEFAULT_LOG_DIR
from logger_lab.logging_kernel.formatters import build_file_formatter
from logger_lab.logging_kernel.handlers import (
    SharedTimedRotatingFileHandler, configure_handler, get_log_dir, share_file_handler,
)


# noinspection PyUnusedLocal
def timed_file_experiment(
    level: int = INFO,
    *,
    log_dir: Path | str = DEFAULT_LOG_DIR,
    filename: str = DEFAULT_FILENAME,
    encoding: str = DEFAULT_ENCODING,
    backup_count: int = DEFAULT_BACKUP_COUNT,
    when: str = "midnight",
    interval: int = 1,
    utc: bool = False,
    at_time: time | None = None,
    logger_name: str | None = None,
    **kwargs: object,
    ) -> list[Handler]:
    """
    Return the shared `TimedRotatingFileHandler` for *log_dir/filename*.

    The file rolls over every *interval* *when* units (``"S"``, ``"M"``, ``"H"``, ``"D"``,
    ``"midnight"`` or ``"W0"``–``"W6"``), keeping *backup_count* old files.  Like the other
    file experiments, the handler has no level (``NOTSET``) because it may be shared.

    Args:
        level:        Accepted for the experiment contract; the logger's level filters instead.
        log_dir:      Directory in which to create the log file.
        filename:     Name of the log file inside *log_dir*.
        encoding:     File encoding.
        backup_count: Old files to keep — with ``"midnight"``, the number of days.
        when:         Rotation unit.  Defaults to ``"midnight"`` (one file per day).
        interval:     How many *when* units between rollovers.
        utc:          Use UTC instead of local time for rollover times and suffixes.
        at_time:      With ``"midnight"`` or ``"W0"``–``"W6"``, the time of day to roll over.
        logger_name:  The logger this is for — passed by the builder; used for sharing.
        **kwargs:     Other file args (``max_bytes``), ignored.
    Returns:
        A single-element list containing the shared `SharedTimedRotatingFileHandler`.
    Raises:
        `LogFileClashError`:
            If another logger already has this file open as a different experiment.
    Example::
        lab().with_theory("TIMED_FILE", when="midnight").with_file_args(backup_count=7).build(__name__)
    """

    log_path = get_log_dir(log_dir) / filename

    handler = share_file_handler(
        log_path,
        kind="TIMED_FILE",
        settings={"encoding": encoding, "backup_count": backup_count, "when": when.upper(),
                  "interval": interval, "utc": utc, "at_time": at_time},
        open_handler=lambda: configure_handler(
            SharedTimedRotatingFileHandler(log_path, when=when, interval=interval, backupCount=backup_count,
                                           encoding=encoding, utc=utc, atTime=at_time),
            NOTSET,
            build_file_formatter(),
        ),
        logger_name=logger_name,
    )

    return [handler]
