"""
File experiment — persistent plain-text file handler.

Writes timestamped, structured plain-text records to a file on disk.
The log directory is created automatically by `get_log_dir()` if it does
not exist — experiments must **never** call `os.makedirs` or
`~pathlib.Path.mkdir` directly.

Each file is opened once per process: every logger writing to the same
path shares one handler (see `share_file_handler()`), so modules can log
to one ``app.log`` at their own levels.

Used by the ``investigator`` profile.
"""

from logging import INFO, NOTSET, Handler
from pathlib import Path

from logger_lab.logging_kernel.formatters import build_file_formatter
from logger_lab.logging_kernel.handlers import SharedFileHandler, configure_handler, get_log_dir, share_file_handler
from logger_lab.logging_kernel.constants import DEFAULT_LOG_DIR, DEFAULT_FILENAME, DEFAULT_ENCODING


# noinspection PyUnusedLocal
def file_experiment(
    level: int = INFO,
    *,
    log_dir: Path | str = DEFAULT_LOG_DIR,
    filename: str = DEFAULT_FILENAME,
    encoding: str = DEFAULT_ENCODING,
    logger_name: str | None = None,
    **kwargs: object,
    ) -> list[Handler]:
    """
    Return the shared `~logging.FileHandler` for *log_dir/filename*.

    The directory is created (including parents) if it does not exist.
    All records are appended to the same file across runs — use
    `rotating_file_experiment()` when you need size-based rotation.

    Note: the handler has no level of its own (``NOTSET``) because it may be
    shared — each logger's own level decides what reaches the file.

    Args:
        level:       Accepted for the experiment contract; the logger's level filters instead.
        log_dir:     Directory in which to create the log file.
                     Defaults to ``logs/`` relative to the cwd.
        filename:    Name of the log file inside *log_dir*.
                     Defaults to ``DEFAULT_FILENAME``.
        encoding:    File encoding.  Defaults to ``"utf-8"``.
        logger_name: The logger this is for — passed by the builder; used for sharing.
        **kwargs:    Other file args, ignored.
    Returns:
        A single-element list containing the shared `SharedFileHandler`.
    Raises:
        `LogFileClashError`:
            If another logger already has this file open as a different experiment.
    Example::
        handlers = file_experiment(logging.WARNING, log_dir=Path("/var/log/myapp"), logger_name=__name__)
        for h in handlers:
            logger.addHandler(h)
    """

    log_path = get_log_dir(log_dir) / filename

    handler = share_file_handler(
        log_path,
        kind="FILE",
        settings={"encoding": encoding},
        open_handler=lambda: configure_handler(
            SharedFileHandler(log_path, encoding=encoding), NOTSET, build_file_formatter(),
        ),
        logger_name=logger_name,
    )

    return [handler]
