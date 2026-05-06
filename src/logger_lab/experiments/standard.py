"""
Standard experiment — Rich console handler.

``standard`` is the default console experiment.  It delegates all
formatting and colour to `rich.logging.RichHandler`, which
produces human-friendly, syntax-highlighted output with automatic
tracebacks.

This is the experiment used by the ``investigator`` profile and the
recommended starting point for interactive development.
"""

from logging import DEBUG, Handler
from rich.logging import RichHandler

from logger_lab.logging_kernel.handlers import configure_handler


# noinspection PyUnusedLocal
def standard_experiment(level: int = DEBUG, **kwargs: object) -> list[Handler]:
    """
    Return a Rich console handler configured at *level*.

    Rich manages its own formatting internally, so no formatter is
    attached — ``_configure_handler`` receives ``formatter=None``.

    Args:
        level:    Logging level for the handler.
                  Defaults to :data:`logging.DEBUG`.
        **kwargs: Reserved for future Rich configuration options
                  (e.g. ``show_path``, ``enable_link_path``).
    Returns:
        A single-element list containing the configured `~rich.logging.RichHandler`.
    Example::
        handlers = standard_experiment(logging.INFO)
        for h in handlers:
            logger.addHandler(h)
    """

    handler = RichHandler(
        rich_tracebacks=True,
        markup=True,
        show_time=True,
        show_level=True,
        show_path=False,
    )

    return [configure_handler(handler, level, formatter=None)]
