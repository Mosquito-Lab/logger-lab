"""
Investigator profile: the everyday development workhorse, console + file.

A Rich console (colors, tracebacks) and a plain-text log file at ``logs/app.log``, so every
record shows in the terminal and stays on disk. Add features on top, e.g.
``.with_feature("ROTATING")`` or ``.with_feature("TIMED", at="02:00")``.
"""

from typing import TYPE_CHECKING

from logger_lab.core.enums import Output, ProfileType
from logger_lab.core.specs import ProfileSpec

if TYPE_CHECKING:  # type-only: the builder imports the registry, which imports this module
    from logger_lab.core.builder import LabBuilder


def investigator(builder: "LabBuilder") -> "LabBuilder":
    """
    Console + file.

    Example::
        logger = lab().with_profile("investigator").build(__name__)
        logger.error("Unexpected response", exc_info=True)
    """

    return builder.with_output(Output.CONSOLE).with_output(Output.FILE)


INVESTIGATOR_SPEC = ProfileSpec(member=ProfileType.INVESTIGATOR, recipe=investigator, summary="console + file")
