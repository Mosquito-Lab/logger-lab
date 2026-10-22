"""
Relay experiment — hand every record to your own callbacks, live.

The ``LIVE`` channel: one `RelayHandler` per subscriber added with
`LabBuilder.with_subscriber(callback, level=None)`.  logger-lab knows nothing about what the
callback does, so it works for a Qt signal, a web socket, a test, anything.

With ``async`` on the same logger, callbacks run on the dispatch worker thread; without it,
on whichever thread logged.  For Qt, pass a signal's ``emit``: Qt delivers it on the
receiver's thread, so the GUI gets every record on the GUI thread.

Used by the ``gui`` profile, alongside ``async``.
"""

import logging
from logging import INFO, NOTSET, Handler
from typing import Callable

from logger_lab.logging_kernel.handlers import configure_handler

Subscriber = Callable[[logging.LogRecord], object]  # Called with each record it lets through


class RelayHandler(logging.Handler):
    """Calls one subscriber with each record.  The record is shared — subscribers must not change it."""

    def __init__(self, callback: Subscriber) -> None:
        """Wrap *callback*."""

        super().__init__()
        self.callback = callback

    def emit(self, record: logging.LogRecord) -> None:
        """Hand *record* to the callback; a callback that raises is reported, never propagated."""

        try:
            self.callback(record)

        except Exception:
            self.handleError(record)


# noinspection PyUnusedLocal
def relay_experiment(
    level: int = INFO,
    *,
    subscribers: tuple[tuple[Subscriber, int | None], ...] = (),
    **kwargs: object,
    ) -> list[Handler]:
    """
    Return one `RelayHandler` per subscriber.

    Each handler gets its subscriber's own level (``None`` → ``NOTSET``, so the logger's
    level decides).  No subscribers, no handlers.

    Args:
        level:       Accepted for the experiment contract; each subscriber's level filters instead.
        subscribers: ``(callback, level)`` pairs from `LabBuilder.with_subscriber()`.
        **kwargs:    File args and the logger name, ignored.
    Returns:
        A list with one `RelayHandler` per subscriber.
    Example::
        lab().with_subscriber(print, level=logging.WARNING).with_experiment("standard").build(__name__)
    """

    return [
        configure_handler(RelayHandler(callback), NOTSET if sub_level is None else sub_level)
        for callback, sub_level in subscribers
    ]
