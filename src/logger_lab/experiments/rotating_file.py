"""
Rotating-file experiment — size-based log rotation.

Writes to a file that rolls over when it reaches *max_bytes*, keeping
*backup_count* older copies.  Designed for long-running processes
where unbounded log growth is a concern.

Rotation naming follows the stdlib convention::

    app.log        ← current
    app.log.1      ← previous
    app.log.2      ← older
    …

Each file is opened once per process: every logger writing to the same
path shares one handler (see `share_file_handler()`), so exactly one
handler ever rotates it — which is what keeps rotation working on Windows.

Used by the ``conspiracy_theorist`` profile alongside ``verbose`` so every
record is captured at maximum detail with automatic housekeeping.
"""

from pathlib import Path
from logging import INFO, NOTSET, Handler

from logger_lab.logging_kernel.formatters import build_file_formatter
from logger_lab.logging_kernel.handlers import (
    SharedRotatingFileHandler, configure_handler, get_log_dir, share_file_handler,
)
from logger_lab.logging_kernel.constants import (DEFAULT_LOG_DIR, DEFAULT_FILENAME, DEFAULT_MAX_BYTES,
                                                 DEFAULT_BACKUP_COUNT, DEFAULT_ENCODING)


# noinspection PyUnusedLocal
def rotating_file_experiment(
    level: int = INFO,
    *,
    log_dir: Path | str = DEFAULT_LOG_DIR,
    filename: str = DEFAULT_FILENAME,
    max_bytes: int = DEFAULT_MAX_BYTES,
    backup_count: int = DEFAULT_BACKUP_COUNT,
    encoding: str = DEFAULT_ENCODING,
    logger_name: str | None = None,
    **kwargs: object,
    ) -> list[Handler]:
    """
    Return the shared `RotatingFileHandler` for *log_dir/filename*.

    Rotates the file when it reaches *max_bytes*, keeping up to
    *backup_count* older copies.  The log directory is created automatically.

    Note: the handler has no level of its own (``NOTSET``) because it may be
    shared — each logger's own level decides what reaches the file.  A
    logger joining an open file with different sizes/encoding gets the
    first settings and a `SharedFileSettingsWarning`.

    Args:
        level:        Accepted for the experiment contract; the logger's level filters instead.
        log_dir:      Directory in which to create the log file.
                      Defaults to ``logs/`` relative to the cwd.
        filename:     Name of the log file inside *log_dir*.
                      Defaults to ``DEFAULT_FILENAME``.
        max_bytes:    File size threshold for rotation, in bytes.
                      Defaults to 5 MiB (``5_242_880``).
        backup_count: Number of rotated files to retain.
                      Defaults to ``3``.
        encoding:     File encoding.  Defaults to ``"utf-8"``.
        logger_name:  The logger this is for — passed by the builder; used for sharing.
        **kwargs:     Other file args, ignored.
    Returns:
        A single-element list containing the shared `SharedRotatingFileHandler`.
    Raises:
        `LogFileClashError`:
            If another logger already has this file open as a different experiment.
    Example::
        handlers = rotating_file_experiment(
            logging.DEBUG,
            log_dir=Path("/var/log/myapp"),
            max_bytes=10_485_760,   # 10 MiB
            backup_count=5,
            logger_name=__name__,
        )
        for h in handlers:
            logger.addHandler(h)
    """

    log_path = get_log_dir(log_dir) / filename

    handler = share_file_handler(
        log_path,
        kind="ROTATING",
        settings={"encoding": encoding, "max_bytes": max_bytes, "backup_count": backup_count},
        open_handler=lambda: configure_handler(
            SharedRotatingFileHandler(log_path, maxBytes=max_bytes, backupCount=backup_count, encoding=encoding),
            NOTSET,
            build_file_formatter(),
        ),
        logger_name=logger_name,
    )

    return [handler]
