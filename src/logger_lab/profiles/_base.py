"""
Shared profile construction base — internal module.

`_build_profile` is the single place where a `logging.Logger` is assembled
from experiment handler factories.

This module is **not** part of the public API.  Import from
``logger_lab.profiles`` instead.
"""

from typing import Callable
from logging import getLogger, Handler, Logger

from logger_lab.logging_kernel.handlers import clear_handlers


def _build_profile(
    name: str,level: int,
    *experiment_factories: Callable[[int], list[Handler]],
    ) -> Logger:
    """
    Shared profile skeleton — the single place where a logger is built.
    Every profile delegates to this function.  It:

    1. Retrieves (or creates) the named logger from the global registry.
    2. Clears any existing handlers to prevent duplicate output.
    3. Calls each *experiment_factory* with *level* and attaches the
       returned handlers in the order supplied.
    4. Sets the logger level and disables propagation to the root logger.

    Args:
        name: Logger name, typically ``__name__``.
        level: Logging level applied to the logger and all attached handlers.
        *experiment_factories: Zero or more experiment factory callables.
        Each must accept ``(level: int, **kwargs)`` and return ``list[logging.Handler]``.
    Returns:
        A fully configured `logging.Logger` with ``propagate = False``.
    Example::
        def investigator(name: str, level: int = DEBUG) -> Logger:
            return _build_profile(name, level, standard_experiment, file_experiment)
    """

    logger = getLogger(name)
    clear_handlers(logger)

    for factory in experiment_factories:

        for handler in factory(level):
            logger.addHandler(handler)

    logger.setLevel(level)
    logger.propagate = False  # Non-negotiable: prevents bubbling to root logger

    return logger
