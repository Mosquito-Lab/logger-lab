"""
Formats: how a record looks. Set with ``with_format(name, on=...)``. One format per output.

| Format   | Fits           | Looks like                                                  |
| -------- | -------------- | ----------------------------------------------------------- |
| ``RICH`` | console        | Rich colors, columns and tracebacks. The console's default  |
| ``TEXT`` | console, file  | Plain lines (see the detail features). The file's default   |
| ``JSON`` | console, file  | One JSON object per line, Mosquito Lab Logging Standard v1.2 |

The outputs do the rendering (`logger_lab.outputs`). A format spec says where it fits.
"""

from logger_lab.core.enums import Format, Output
from logger_lab.core.specs import FormatSpec

RICH_SPEC = FormatSpec(member=Format.RICH, fits=frozenset({Output.CONSOLE}))
TEXT_SPEC = FormatSpec(member=Format.TEXT, fits=frozenset({Output.CONSOLE, Output.FILE}))
JSON_SPEC = FormatSpec(member=Format.JSON, fits=frozenset({Output.CONSOLE, Output.FILE}))

__all__ = ["RICH_SPEC", "TEXT_SPEC", "JSON_SPEC"]
