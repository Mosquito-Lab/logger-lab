"""
Console output: feedback for a person at a terminal.

Rich by default (colors, aligned columns, Rich tracebacks). ``TEXT`` gives plain lines, and
``JSON`` gives one JSON object per line. The detail features change how much is shown:

* ``MINIMAL``: level and message;
* (default): time, level and message;
* ``VERBOSE``: also the logger name and where the record came from.

Options: ``stream="stderr"`` (default) or ``"stdout"``. stderr keeps stdout free for a
program's own output, which is the usual logging convention.

A ``TEXT`` or ``JSON`` console takes the stream when it is built, as `StreamHandler` does.
A Rich console looks it up on every record. So if ``sys.stderr`` is replaced after the
build (a test capturing output, say), only a Rich console writes to the new one.

The handler has no level of its own (``NOTSET``), so the logger's level is the one switch.
A ``logger.setLevel()`` after the build reaches the console too.

Rich markup in messages is off, so text like ``[/usr/bin]`` prints as it is. To style one
record, pass ``extra={"markup": True}``.
"""

import sys
from logging import NOTSET, Formatter, Handler, LogRecord, StreamHandler

from rich.console import Console
from rich.logging import RichHandler

from logger_lab.core.enums import Format, Output
from logger_lab.core.specs import OutputPlan, OutputSpec
from logger_lab.logging_kernel.errors import CompositionError
from logger_lab.logging_kernel.formatters import JSONFormatter, text_formatter
from logger_lab.logging_kernel.handlers import configure_handler

STREAMS = ("stderr", "stdout")  # Accepted values for the stream option


class LabRichHandler(RichHandler):
    """
    A `RichHandler` that never raises out of a logging call.

    Rich formats and renders the message outside its own error handling. So a bad format
    call such as ``logger.info("%d", "x")`` would raise in the caller. Every stdlib handler
    reports that through `handleError` instead, and so does this one.
    """

    def emit(self, record: LogRecord) -> None:
        """Render *record* like `RichHandler`, reporting any failure instead of raising it."""

        # noinspection PyBroadException
        try:
            super().emit(record)

        except Exception:  # Any rendering error: a logging call must never raise
            self.handleError(record)


def check_console(plan: OutputPlan) -> None:
    """Reject a stream other than ``"stderr"``/``"stdout"``."""

    if plan.options["stream"] not in STREAMS:
        raise CompositionError(f"console stream={plan.options['stream']!r}: use 'stderr' or 'stdout'")


def build_console(plan: OutputPlan) -> list[Handler]:
    """
    Return the console handler for *plan*: Rich, plain text or JSON, at the plan's detail.

    Args:
        plan: The console's options, features and format, from the builder.
    Returns:
        A single-element list with the configured handler.
    Example::
        lab().with_output("console").with_feature("VERBOSE").build(__name__)
    """

    to_stderr = plan.options["stream"] == "stderr"

    if plan.format is Format.RICH:
        handler = LabRichHandler(
            console=Console(stderr=to_stderr),
            rich_tracebacks=True,
            markup=False,  # A message is text; brackets in it must never be parsed (or raise)
            show_time=plan.detail != "minimal",
            show_level=True,
            show_path=plan.detail == "verbose",
        )
        formatter = Formatter("%(name)s: %(message)s") if plan.detail == "verbose" else None

        return [configure_handler(handler, NOTSET, formatter)]

    stream = sys.stderr if to_stderr else sys.stdout
    formatter = JSONFormatter() if plan.format is Format.JSON else text_formatter(plan.detail)

    return [configure_handler(StreamHandler(stream), NOTSET, formatter)]


CONSOLE_SPEC = OutputSpec(
    member=Output.CONSOLE,
    build=build_console,
    options={"stream": "stderr"},
    formats=frozenset({Format.RICH, Format.TEXT, Format.JSON}),
    default_format=Format.RICH,
    check=check_console,
)
