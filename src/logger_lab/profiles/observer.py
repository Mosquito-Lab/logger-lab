"""
Observer profile — production-safe, low-noise logging.

Applies a single `minimalist_experiment()` handler so only warnings, errors, and
critical events surface.  The observer stays quiet until something actually matters.
"""

from logging import WARNING, Logger

from logger_lab.profiles.base import build_profile
from logger_lab.experiments.minimalist import minimalist_experiment

OBSERVER_EXPERIMENTS = (minimalist_experiment,)  # Built from, in order: one console


def observer(name: str, level: int = WARNING, **kwargs: object) -> Logger:
    """
    Return a logger configured for production-safe, low-noise output.

    Uses the ``minimalist`` experiment — plain ``LEVEL: message`` format,
    default level `logging.WARNING`.

    Args:
        name:  Logger name, typically ``__name__``.
        level: Logging level.  Defaults to `logging.WARNING`.
        **kwargs: File args (``log_dir``, ``filename``, …) forwarded to every experiment.
    Returns:
        A configured `logging.Logger` with ``propagate = False``.
    Example::
        logger = observer(__name__)
        logger.warning("Disk usage above 90 %%")   # → "WARNING: Disk usage above 90 %"
        logger.debug("This is silent")              # → (nothing)
    """

    return build_profile(name, level, *OBSERVER_EXPERIMENTS, **kwargs)
