"""
Detail features: how much each line shows, on the console and in files.

| Detail             | Console (Rich)                    | File / plain text                                   |
| ------------------ | --------------------------------- | --------------------------------------------------- |
| ``MINIMAL``        | level, message                    | ``INFO: Saved``                                     |
| (default)          | time, level, message              | ``2026-05-05 10:00:00 - app - INFO - Saved``        |
| ``VERBOSE``        | + logger name, ``file:line``      | ``… - app - INFO - store.save:42 - Saved``          |

Only one detail feature per output, because they share the ``detail`` group. JSON always
carries every field, so detail features don't apply to it. Detail changes what is *shown*,
never what is *logged*. Use ``with_level()`` for that.
"""

from logger_lab.core.enums import Feature, Format, Output
from logger_lab.core.specs import FeatureSpec

DETAIL_OUTPUTS = frozenset({Output.CONSOLE, Output.FILE})  # The outputs whose lines have a detail level
DETAIL_FORMATS = frozenset({Format.RICH, Format.TEXT})  # The formats detail changes. JSON always has every field

MINIMAL_SPEC = FeatureSpec(member=Feature.MINIMAL, fits=DETAIL_OUTPUTS, group="detail", formats=DETAIL_FORMATS)
VERBOSE_SPEC = FeatureSpec(member=Feature.VERBOSE, fits=DETAIL_OUTPUTS, group="detail", formats=DETAIL_FORMATS)
