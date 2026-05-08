"""
File experiment — persistent plain-text file handler.

Writes timestamped, structured plain-text records to a file on disk.
The log directory is created automatically by `get_log_dir()` if it does
not exist — experiments must **never** call `os.makedirs` or
`~pathlib.Path.mkdir` directly.

Used by the ``investigator`` and ``conspiracy_theorist`` profiles.
"""

from logging import DEBUG, Handler, FileHandler
from pathlib import Path

from logger_lab.logging_kernel.formatters import build_file_formatter
from logger_lab.logging_kernel.handlers import configure_handler, get_log_dir
from logger_lab.logging_kernel.constants import DEFAULT_LOG_DIR, DEFAULT_FILENAME, DEFAULT_ENCODING


# noinspection PyUnusedLocal
def file_experiment(
        level: int = DEBUG,
        *,
        log_dir: Path | str = DEFAULT_LOG_DIR,
        filename: str       = DEFAULT_FILENAME,
        encoding: str       = DEFAULT_ENCODING,
        **kwargs: object,
) -> list[Handler]:
    """
    Return a `~logging.FileHandler` that writes to *log_dir/filename*.

    The directory is created (including parents) if it does not exist.
    All records are appended to the same file across runs — use
    `rotating_file_experiment()`
    when you need size-based rotation.

    Args:
        level:    Logging level for the handler.
                  Defaults to :data:`logging.DEBUG`.
        log_dir:  Directory in which to create the log file.
                  Defaults to ``logs/`` relative to the cwd.
        filename: Name of the log file inside *log_dir*.
                  Defaults to ``DEFAULT_FILENAME``.
        encoding: File encoding.  Defaults to ``"utf-8"``.
        **kwargs: Reserved for future extension.
    Returns:
        A single-element list containing the configured
        `~logging.FileHandler`.
    Example::
        handlers = file_experiment(logging.WARNING, log_dir=Path("/var/log/myapp"))
        for h in handlers:
            logger.addHandler(h)
    """

    log_path = get_log_dir(log_dir) / filename
    formatter = build_file_formatter()

    handler = FileHandler(log_path, encoding=encoding)

    return [configure_handler(handler, level, formatter)]
