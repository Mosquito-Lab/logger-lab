"""
Conspiracy Theorist profile: verbose console output plus a size-rotated log
file.  Every record is captured at full context detail and automatically
rotated so disk usage stays bounded.

Use when you need to sift through the grains later and leave no stone
unturned.
"""

from logging import INFO, Logger

from logger_lab.experiments.rotating_file import rotating_file_experiment
from logger_lab.experiments.verbose import verbose_experiment
from logger_lab.profiles.base import build_profile

CONSPIRACY_THEORIST_EXPERIMENTS = (verbose_experiment, rotating_file_experiment)  # Built from, in order: one console, one file


def conspiracy_theorist(name: str, level: int = INFO, **kwargs: object) -> Logger:
    """
    Return a logger that captures everything, everywhere, all at once.

    Experiments applied (in order):
    * ``verbose``       — full call-site context on every console line.
    * ``rotating_file`` — size-rotated log at ``logs/app.log`` (5 MiB, 3 backups).

    Args:
        name:  Logger name, typically ``__name__``.
        level: Logging level.  Defaults to `logging.INFO`.
        **kwargs: File args (``log_dir``, ``filename``, …) forwarded to every experiment.
    Returns:
        A configured `logging.Logger` with ``propagate = False``.
    Example::
        logger = conspiracy_theorist(__name__)
        logger.debug("Raw response: %s", raw)   # captured on the console and in the rotating file
    """

    return build_profile(name, level, *CONSPIRACY_THEORIST_EXPERIMENTS, **kwargs)
