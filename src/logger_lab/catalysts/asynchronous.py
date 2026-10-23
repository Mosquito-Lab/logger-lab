"""
``ASYNC`` catalyst: move formatting and writing off the calling thread.

The builder hands it the logger's built outputs, and the logger ends up with one
`AsyncHandler` that queues each record and returns at once. A single worker thread for the
whole process formats and writes them, in order, to those outputs.

Use it wherever the caller shouldn't wait on disk or console: GUI threads, asyncio code,
hot loops. Tracebacks survive (unlike the stdlib `QueueHandler`), and queued records are
written before the interpreter exits. Call `logger_lab.drain()` to wait for them yourself.
How it works and its limits: ``docs/Feedback_Guide.md``.

Used by the ``gui`` profile. It is in the ``dispatch`` group, so a logger takes one dispatcher.
"""

from logging import NOTSET, Handler

from logger_lab.core.enums import Catalyst
from logger_lab.core.specs import CatalystSpec
from logger_lab.logging_kernel.dispatch import AsyncHandler
from logger_lab.logging_kernel.errors import BuilderError
from logger_lab.logging_kernel.handlers import configure_handler


# noinspection PyUnusedLocal
def build_async(handlers: list[Handler], *, logger_name: str, options: dict[str, object]) -> list[Handler]:
    """
    Return the one `AsyncHandler` that dispatches to *handlers* on the worker thread.

    It owns *handlers*: it delivers to them and releases them when it is released itself.

    Args:
        handlers:    The logger's built output handlers.
        logger_name: The logger this is for. Used to release shared files correctly.
        options:     None today.
    Returns:
        A single-element list containing the `AsyncHandler`.
    Raises:
        `BuilderError`: If there are no outputs to dispatch to.
    Example::
        lab().with_profile("investigator").with_catalyst("ASYNC").build(__name__)
    """

    if not handlers:
        raise BuilderError(
            f"logger '{logger_name}' has the 'ASYNC' catalyst but nothing for it to dispatch to. "
            f"Add an output (.with_output()) or a profile"
        )

    return [configure_handler(AsyncHandler(handlers, logger_name), NOTSET)]


ASYNC_SPEC = CatalystSpec(member=Catalyst.ASYNC, build=build_async, group="dispatch")
