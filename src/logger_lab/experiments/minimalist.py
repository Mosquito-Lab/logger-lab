"""
Minimalist experiment — low-noise plain-text console handler.

Emits only the level name and message.  Intended for production
environments where log volume must be kept low and only actionable
signals (warnings, errors, critical events) are surfaced.

Default level is `logging.WARNING`, not `logging.DEBUG`,
because minimalism means silence until something matters.

Used by the ``observer`` profile.
"""

from logging import WARNING, Handler, Formatter, StreamHandler

from logger_lab.logging_kernel.handlers import configure_handler


# noinspection PyUnusedLocal
def minimalist_experiment(level: int = WARNING, **kwargs: object) -> list[Handler]:
    """
    Return a low-noise `~logging.StreamHandler`.

    The format is deliberately terse — ``LEVEL: message`` — so logs
    are readable at a glance without parsing timestamps or call-site
    metadata.

    Args:
        level:    Logging level for the handler.
                  Defaults to `logging.WARNING`.
        **kwargs: Reserved for future extension.
    Returns:
        A single-element list containing the configured
        `~logging.StreamHandler`.
    Example::
        handlers = minimalist_experiment()          # WARNING and above
        handlers = minimalist_experiment(logging.ERROR)  # errors only
    """

    formatter = Formatter(fmt="%(levelname)s: %(message)s")
    handler = StreamHandler()

    return [configure_handler(handler, level, formatter)]
