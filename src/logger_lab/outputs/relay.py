"""
Relay output: feedback for a live UI or service. Every record goes to your own callbacks.

One `RelayHandler` per subscriber added with `LabBuilder.with_subscriber(callback, level=None)`
(which brings this output with it). logger-lab knows nothing about what the callback does,
so it works for a Qt signal, a web socket, a test, anything.

With the ``ASYNC`` catalyst, callbacks run on the dispatch worker thread. Without it, they
run on whichever thread logged. For Qt, pass a signal's ``emit``: Qt delivers it on the
receiver's thread, so the GUI gets every record on the GUI thread. See ``docs/Feedback_Guide.md``.

No options and no formats: subscribers get the `logging.LogRecord` itself.

A record logged *inside* a subscriber (an echo) still reaches files and consoles, but no
subscriber gets it. Without that guard, a subscriber that logs to its own logger would
call itself without end. The guard covers the ``ASYNC`` path too.
"""

import logging
import threading
from logging import NOTSET, Handler

from logger_lab.core.enums import Output
from logger_lab.core.specs import OutputPlan, OutputSpec, Subscriber
from logger_lab.logging_kernel.dispatch import SUBSCRIBER_CALL, in_subscriber, is_echo
from logger_lab.logging_kernel.handlers import configure_handler


class RelayHandler(logging.Handler):
    """Calls one subscriber with each record. The record is shared, so subscribers must not change it."""

    def __init__(self, callback: Subscriber) -> None:
        """Wrap *callback*."""

        super().__init__()
        self.callback = callback
        # One call at a time, kept apart from the handler's own lock. Re-entrant, so a slip can't deadlock.
        self.calls_lock = threading.RLock()

    def handle(self, record: logging.LogRecord) -> bool:
        """
        Filter *record*, then emit it without holding the handler's lock.

        The stdlib holds the handler lock around `emit`, which here means for as long as the
        subscriber runs. `logging.shutdown()` takes every handler's lock at exit, so a stuck
        subscriber would hang the exit. Calls are serialized by *calls_lock* instead.
        """

        result = self.filter(record)

        if isinstance(result, logging.LogRecord):  # Python 3.12+: a filter may return a new record
            record = result

        if result:
            self.emit(record)

        return result  # Like the stdlib: the filter's result (a record on 3.12+, which is truthy)

    def emit(self, record: logging.LogRecord) -> None:
        """
        Hand *record* to the callback. A callback that raises is reported, never propagated.

        An echo, a record logged inside a subscriber, is skipped (see the module docstring).
        """

        if in_subscriber() or is_echo(record):
            return

        with self.calls_lock:
            SUBSCRIBER_CALL.active = True

            # noinspection PyBroadException
            try:
                self.callback(record)

            except Exception:  # Any subscriber error: a logging call must never raise
                self.handleError(record)

            finally:
                SUBSCRIBER_CALL.active = False


def build_relay(plan: OutputPlan) -> list[Handler]:
    """
    Return one `RelayHandler` per subscriber, each at its subscriber's level (``None`` → the logger's).

    Args:
        plan: The relay's subscribers, from the builder.
    Returns:
        A list with one handler per subscriber (empty with no subscribers).
    Example::
        lab().with_output("console").with_subscriber(alerts.append, level="ERROR").build(__name__)
    """

    return [
        configure_handler(RelayHandler(callback), NOTSET if level is None else level)
        for callback, level in plan.subscribers
    ]


RELAY_SPEC = OutputSpec(member=Output.RELAY, build=build_relay)
