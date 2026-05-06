"""
Rotating-file experiment — size-based log rotation.

Writes to a file that rolls over when it reaches *max_bytes*, keeping
*backup_count* compressed copies.  Designed for long-running processes
where unbounded log growth is a concern.

Rotation naming follows the stdlib convention::

    app.log        ← current
    app.log.1      ← previous
    app.log.2      ← older
    …

Used by the ``conspiracy_theorist`` profile alongside ``verbose`` and
``file`` so every record is captured at maximum detail with automatic
housekeeping.
"""

from pathlib import Path
from logging import DEBUG, Handler
from logging.handlers import RotatingFileHandler

from logger_lab.logging_kernel.formatters import build_file_formatter
from logger_lab.logging_kernel.handlers import configure_handler, get_log_dir

#: Default log file name.
_DEFAULT_FILENAME = "app.log"

#: Default log directory.
_DEFAULT_LOG_DIR = Path("logs")

#: Default maximum file size before rotation: 5 MiB.
_DEFAULT_MAX_BYTES: int = 5 * 1024 * 1024

#: Default number of rotated backup files to retain.
_DEFAULT_BACKUP_COUNT: int = 3


# noinspection PyUnusedLocal
def rotating_file_experiment(
        level: int = DEBUG,
        *,
        log_dir: Path | str = _DEFAULT_LOG_DIR,
        filename: str = _DEFAULT_FILENAME,
        max_bytes: int = _DEFAULT_MAX_BYTES,
        backup_count: int = _DEFAULT_BACKUP_COUNT,
        encoding: str = "utf-8",
        **kwargs: object,
) -> list[Handler]:
    """
    Return a `RotatingFileHandler`.

    Rotates *log_dir/filename* when it reaches *max_bytes*, retaining
    up to *backup_count* compressed copies.  The log directory is
    created automatically.

    Args:
        level:        Logging level for the handler.
                      Defaults to :data:`logging.DEBUG`.
        log_dir:      Directory in which to create the log file.
                      Defaults to ``logs/`` relative to the cwd.
        filename:     Name of the log file inside *log_dir*.
                      Defaults to ``"app.log"``.
        max_bytes:    File size threshold for rotation, in bytes.
                      Defaults to 5 MiB (``5_242_880``).
        backup_count: Number of rotated files to retain.
                      Defaults to ``3``.
        encoding:     File encoding.  Defaults to ``"utf-8"``.
        **kwargs:     Reserved for future extension.
    Returns:
        A single-element list containing the configured
        `RotatingFileHandler`.
    Example::
        handlers = rotating_file_experiment(
            logging.DEBUG,
            log_dir=Path("/var/log/myapp"),
            max_bytes=10_485_760,   # 10 MiB
            backup_count=5,
        )
        for h in handlers:
            logger.addHandler(h)
    """

    log_path = get_log_dir(log_dir) / filename
    formatter = build_file_formatter()

    handler = RotatingFileHandler(
        log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding=encoding,
    )

    return [configure_handler(handler, level, formatter)]
