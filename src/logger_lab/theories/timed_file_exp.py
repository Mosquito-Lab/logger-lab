"""
Timed-file theory — time-based log rotation (placeholder stage).

Planned mechanism: `logging.handlers.TimedRotatingFileHandler`, rolling the
file over on a schedule (e.g. ``when="midnight"``) instead of by size, built
through `get_log_dir()` and the file args like the other file experiments.
Writes to the FILE channel.

Not registered yet: selecting ``TheoryType.TIMED_FILE`` raises
`TheoryNotFoundError` until this factory works and is registered with
`register_theory()` (see the theory lifecycle in the Standards doc).
"""

from logging import WARNING, Handler


# noinspection PyUnusedLocal
def timed_file_experiment(level: int = WARNING, **kwargs: object) -> list[Handler]:
    """
    Return a `TimedRotatingFileHandler` — not implemented yet.

    Args:
        level:    Logging level for the handler.
        **kwargs: File args, plus ``when``/``interval``/``utc`` theory options.
    Raises:
        `NotImplementedError`: Always, until the theory reaches the trial stage.
    """

    raise NotImplementedError("timed_file_experiment is still a placeholder theory")
