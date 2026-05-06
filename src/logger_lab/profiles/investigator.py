"""
Investigator profile — everyday development workhorse.

Combines a Rich console handler (``standard``) with a persistent file
handler (``file``) so every log record appears in both the terminal —
with colour and traceback support — and a timestamped log file on disk.
"""

from logging import DEBUG, Logger

from logger_lab.experiments.file import file_experiment
from logger_lab.experiments.standard import standard_experiment
from logger_lab.profiles._base import _build_profile


def investigator(name: str, level: int = DEBUG) -> Logger:
    """
    Return a logger with Rich console + persistent file output.
    Experiments applied (in order):

    * ``standard`` — Rich console handler, colourised and traceback-aware.
    * ``file``     — FileHandler writing to ``logs/app.log``.

    Args:
        name:  Logger name, typically ``__name__``.
        level: Logging level.  Defaults to `logging.DEBUG`.
    Returns:
        A configured `logging.Logger` with ``propagate = False``.
    Example::
        logger = investigator(__name__)
        logger.debug("Inspecting payload: %s", payload)
        logger.error("Unexpected response", exc_info=True)
    """

    return _build_profile(name, level, standard_experiment, file_experiment)
