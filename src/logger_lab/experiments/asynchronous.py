"""
Async experiment — move formatting and writing off the calling thread.

Not an output of its own: ``async`` is the logger's **dispatcher** (the ``DISPATCH``
channel).  The builder hands it the logger's other handlers, and the logger ends up with
one `AsyncHandler` that queues each record and returns at once.  A single worker thread for
the whole process formats and writes them, in order, to those outputs.

Use it wherever the caller shouldn't wait on disk or console: GUI threads, asyncio code,
hot loops.  Tracebacks survive (unlike the stdlib `QueueHandler`), and queued records are
written before the interpreter exits.  Call `logger_lab.logging_kernel.drain()` to wait for
them yourself.

Used by the ``gui`` profile.  Promoted from the ``ASYNC`` theory.
"""

from logging import INFO, NOTSET, Handler

from logger_lab.logging_kernel.dispatch import AsyncHandler, dispatcher
from logger_lab.logging_kernel.errors import BuilderError
from logger_lab.logging_kernel.handlers import configure_handler


# noinspection PyUnusedLocal
@dispatcher
def async_experiment(
    level: int = INFO,
    *,
    handlers: list[Handler] | None = None,
    logger_name: str | None = None,
    **kwargs: object,
    ) -> list[Handler]:
    """
    Return the one `AsyncHandler` that dispatches to *handlers* on the worker thread.

    Called by the builder (or `build_profile`) after the logger's outputs are built — not
    usually by hand.  The returned handler owns *handlers*: it delivers to them and releases
    them when it is released itself.

    Args:
        level:       Accepted for the experiment contract; the logger's level filters instead.
        handlers:    The logger's built output handlers to dispatch to.
        logger_name: The logger this is for — used to release shared files correctly.
        **kwargs:    File args and subscribers, ignored.
    Returns:
        A single-element list containing the `AsyncHandler`.
    Raises:
        `BuilderError`: If there are no outputs to dispatch to.
    Example::
        logger = lab().with_experiment("ROTATING").with_experiment("ASYNC").build(__name__)
    """

    if not handlers:
        raise BuilderError(
            logger_name or "<unnamed>",
            reason=f"logger '{logger_name}' queues 'ASYNC' with no output to dispatch to — "
                   f"add a console, file, json or relay experiment (or a profile) alongside it.",
        )

    return [configure_handler(AsyncHandler(handlers, logger_name), NOTSET)]
