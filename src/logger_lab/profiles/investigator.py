"""
Investigator profile — everyday development workhorse.

Combines a Rich console handler (``standard``) with a persistent file
handler (``file``) so every log record appears in both the terminal —
with color and traceback support — and a timestamped log file on disk.
"""

from logging import INFO, Logger

from logger_lab.experiments.file import file_experiment
from logger_lab.experiments.standard import standard_experiment
from logger_lab.profiles.base import build_profile

INVESTIGATOR_EXPERIMENTS = (standard_experiment, file_experiment)  # Built from, in order: one console, one file


def investigator(name: str, level: int = INFO, **kwargs: object) -> Logger:
    """
    Return a logger with Rich console + persistent file output.
    Experiments applied (in order):

    * ``standard`` — Rich console handler, colorized and traceback-aware.
    * ``file``     — FileHandler writing to ``logs/app.log``.

    Args:
        name:  Logger name, typically ``__name__``.
        level: Logging level.  Defaults to `logging.INFO`.
        **kwargs: File args (``log_dir``, ``filename``, …) forwarded to every experiment.
    Returns:
        A configured `logging.Logger` with ``propagate = False``.
    Example::
        logger = investigator(__name__)
        logger.debug("Inspecting payload: %s", payload)
        logger.error("Unexpected response", exc_info=True)
    """

    return build_profile(name, level, *INVESTIGATOR_EXPERIMENTS, **kwargs)
