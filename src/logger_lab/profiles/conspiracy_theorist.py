"""
Conspiracy Theorist profile: verbose console output, a persistent plain-text
file, *and* a rotating file handler.  Every record is captured at full
context detail and automatically rotated so disk usage stays bounded.

Use when you need to sift through the grains later and leave no stone
unturned.
"""

from logging import DEBUG, Logger

from logger_lab.experiments.file import file_experiment
from logger_lab.experiments.rotating_file import rotating_file_experiment
from logger_lab.experiments.verbose import verbose_experiment
from logger_lab.profiles._base import _build_profile


def conspiracy_theorist(name: str, level: int = DEBUG) -> Logger:
    """
    Return a logger that captures everything, everywhere, all at once.

    Experiments applied (in order):
    * ``verbose``       — full call-site context on every console line.
    * ``file``          — persistent plain-text log at ``logs/app.log``.
    * ``rotating_file`` — size-rotated log at ``logs/app.log`` (5 MiB, 3 backups).

    Args:
        name:  Logger name, typically ``__name__``.
        level: Logging level.  Defaults to `logging.DEBUG`.
    Returns:
        A configured `logging.Logger` with ``propagate = False``.
    Example::
        logger = conspiracy_theorist(__name__)
        logger.debug("Raw response: %s", raw)   # captured in all three destinations
    """

    return _build_profile(
        name, level,
        verbose_experiment, file_experiment, rotating_file_experiment,
    )
