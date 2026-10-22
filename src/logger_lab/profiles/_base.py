"""
Shared profile construction base — internal module.

`_build_profile` is the single place where a profile function assembles its
`logging.Logger` from experiment handler factories.  (The builder builds a
profile's declared experiments itself; this is the direct-call path.)

This module is **not** part of the public API.  Import from
``logger_lab.profiles`` instead.
"""

from functools import partial
from typing import Callable
from logging import getLogger, Handler, Logger

from logger_lab.logging_kernel.handlers import install_handlers


def _build_profile(
    name: str, level: int,
    *experiment_factories: Callable[..., list[Handler]],
    **kwargs: object,
    ) -> Logger:
    """
    Shared profile skeleton — the single place where a profile function builds its logger.
    Every profile delegates to this function.  It:

    1. Retrieves (or creates) the named logger from the global registry.
    2. Calls each *experiment_factory* with *level*, ``**kwargs`` and the
       logger's name (for file sharing), then swaps the new handlers onto
       the logger in one step and releases the old ones (`install_handlers`).
    3. Sets the logger level and disables propagation to the root logger.

    Thread-safe, like `LabBuilder.build()`.

    Args:
        name: Logger name, typically ``__name__``.
        level: Logging level applied to the logger.
        *experiment_factories: Zero or more experiment factory callables.
        Each must accept ``(level: int, **kwargs)`` and return ``list[logging.Handler]``.
        **kwargs: Forwarded to every factory — e.g. the file args from
        `LabBuilder.with_file_args()`. Factories ignore what they don't use.
    Returns:
        A fully configured `logging.Logger` with ``propagate = False``.
    Example::
        def investigator(name: str, level: int = DEBUG, **kwargs: object) -> Logger:
            return _build_profile(name, level, standard_experiment, file_experiment, **kwargs)
    """

    logger = getLogger(name)
    factory_kwargs = {**kwargs, "logger_name": name}

    install_handlers(logger, [partial(factory, level, **factory_kwargs) for factory in experiment_factories])

    logger.setLevel(level)
    logger.propagate = False  # Non-negotiable: prevents bubbling to root logger

    return logger
