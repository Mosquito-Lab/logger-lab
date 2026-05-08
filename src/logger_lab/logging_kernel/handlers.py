import logging

from pathlib import Path

from logger_lab.logging_kernel.constants import DEFAULT_LOG_DIR
from logger_lab.logging_kernel.errors import LogDirectoryError


# Handler guard
def clear_handlers(logger: logging.Logger) -> None:
    """Remove all handlers from *logger* to prevent duplicate log output.

    Call this at the start of every profile and experiment that attaches
    new handlers.  It is idempotent — safe to call on a fresh logger.

    Args:
        logger: The logger whose handler list will be cleared.
    """

    logger.handlers.clear()


# Experiment skeleton — shared handler configuration
def configure_handler(
        handler: logging.Handler,
        level: int,
        formatter: logging.Formatter | None = None,
    ) -> logging.Handler:
    """Apply *level* and *formatter* to *handler* and return it.

    This is the **shared experiment skeleton**.  Every experiment calls
    this for each handler it creates so the configuration contract is
    enforced in one place:

    1. Set the logging level on the handler.
    2. Attach the formatter (if supplied; Rich handlers manage their own).

    Args:
        handler:   Any :class:`logging.Handler` subclass.
        level:     Standard :mod:`logging` level constant.
        formatter: Pre-built formatter to attach, or ``None`` for handlers
                   that manage their own formatting (e.g. ``RichHandler``).

    Returns:
        The same *handler* instance, mutated in place, for convenient
        one-liner use inside experiment functions::

            return [_configure_handler(RichHandler(), level)]
    """

    handler.setLevel(level)

    if formatter is not None:
        handler.setFormatter(formatter)

    return handler


# File-system helpers
def get_log_dir(path: Path | str = DEFAULT_LOG_DIR) -> Path:
    """
    Ensure the log directory exists and return it as a :class:`~pathlib.Path`.

    Creates the directory (and any missing parents) if it does not exist.
    This is the **single place** where file-based experiments create the
    log directory; neither ``file_experiment`` nor
    ``rotating_file_experiment`` should call :func:`os.makedirs` or
    :meth:`~pathlib.Path.mkdir` directly.

    Args:
        path: Directory path, as a string or `Path`.
              Defaults to ``logs/`` relative to the current working directory.
    Returns:
        The resolved `Path` to the log directory.
    Raises:
        `LogDirectoryError`:
            If the directory cannot be created or accessed (e.g. permission
            denied). The original `OSError` is chained as ``__cause__``.
    Example::
        handler = FileHandler(get_log_dir("var/log/myapp") / "app.log")
    """

    log_dir = Path(path)

    try:
        log_dir.mkdir(parents=True, exist_ok=True)

    except OSError as err:
        raise LogDirectoryError(log_dir, str(err)) from err

    return log_dir
