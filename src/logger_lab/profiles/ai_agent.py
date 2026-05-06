"""
AI Agent profile — structured JSON output for machine consumption.

Applies a single `ai_experiment` handler that serialises every record
to a JSON object conforming to the Mosquito Lab Logging Standard v1.
Output is designed to be ingested directly by LLM APIs, log aggregators,
and automated pipelines.

Pair with `log_event` to attach ``event``, ``context``, and ``tags`` fields
to individual records.
"""

from logging import DEBUG, Logger

from logger_lab.experiments.ai import ai_experiment
from logger_lab.profiles._base import _build_profile


def ai_agent(name: str, level: int = DEBUG) -> Logger:
    """
    Return a logger that emits structured JSON to stderr.

    Experiments applied:
    * ``ai`` — `~logging.StreamHandler` with `JSONFormatter`.

    Args:
        name:  Logger name, typically ``__name__``.
        level: Logging level.  Defaults to `logging.DEBUG`.
    Returns:
        A configured `logging.Logger` with ``propagate = False``.
    Example::
        from logger_lab.logging_kernel import log_event

        logger = ai_agent(__name__)
        log_event(
            logger, logging.INFO, "Tool call dispatched",
            event="tool_dispatch",
            context={"tool": "web_search", "query": "latest AI news"}
        )
    """

    return _build_profile(name, level, ai_experiment)
