"""
AI experiment — structured JSON console handler.

Produces one JSON object per log record conforming to the
**Mosquito Lab Logging Standard v1**.  Output is machine-readable and
suitable for ingestion by LLM APIs, log aggregators, and automated
pipelines.

Pair with `log_event()` to inject ``event``, ``context``, and ``tags`` fields
into the JSON payload without mutating ``extra`` by hand.

Used by the ``ai_agent`` profile.
"""

from logging import DEBUG, Handler, StreamHandler

from logger_lab.logging_kernel.formatters import JSONFormatter
from logger_lab.logging_kernel.handlers import configure_handler


# noinspection PyUnusedLocal
def ai_experiment(level: int = DEBUG, **kwargs: object) -> list[Handler]:
    """
    Return a `StreamHandler` with `JSONFormatter`.

    Every record is serialised to a single-line JSON object.  Stderr is
    used as the stream so structured output is separate from any
    application stdout.

    Args:
        level:    Logging level for the handler.
                  Defaults to `logging.DEBUG`.
        **kwargs: Reserved for future extension.
    Returns:
        A single-element list containing the configured
        `StreamHandler`.
    Example::
        handlers = ai_experiment(logging.INFO)
        for h in handlers:
            logger.addHandler(h)

        # Then emit a structured event:
        from logger_lab.logging_kernel import log_event
        log_event(
            logger, logging.INFO, "Inference complete",
            event="inference_done",
            context={"tokens": 512, "model": "claude-sonnet"}
        )
    """

    handler = StreamHandler()

    return [configure_handler(handler, level, JSONFormatter())]
