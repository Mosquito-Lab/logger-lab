"""
Observer profile — production-safe, low-noise logging.

Applies a single `minimalist_experiment()` handler so only warnings, errors, and
critical events surface.  The observer stays quiet until something actually matters.
"""

from logging import WARNING, Logger

from logger_lab.profiles._base import _build_profile
from logger_lab.experiments.minimalist import minimalist_experiment


def observer(name: str, level: int = WARNING) -> Logger:
    """
    Return a logger configured for production-safe, low-noise output.

    Uses the ``minimalist`` experiment — plain ``LEVEL: message`` format,
    default level `logging.WARNING`.

    Args:
        name:  Logger name, typically ``__name__``.
        level: Logging level.  Defaults to `logging.WARNING`.
    Returns:
        A configured `logging.Logger` with ``propagate = False``.
    Example::
        logger = observer(__name__)
        logger.warning("Disk usage above 90 %%")   # → "WARNING: Disk usage above 90 %"
        logger.debug("This is silent")              # → (nothing)
    """

    return _build_profile(name, level, minimalist_experiment)
