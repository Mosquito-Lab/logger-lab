"""
Conspiracy Theorist profile: capture everything, everywhere, all at once.

A console and a size-rotated file, both with the ``VERBOSE`` detail feature (module,
function and line on every record), so disk use stays bounded while nothing is missed.
"""

from typing import TYPE_CHECKING

from logger_lab.core.enums import Feature, Output, ProfileType
from logger_lab.core.specs import ProfileSpec

if TYPE_CHECKING:  # type-only: the builder imports the registry, which imports this module
    from logger_lab.core.builder import LabBuilder


def conspiracy_theorist(builder: "LabBuilder") -> "LabBuilder":
    """
    Console + file + VERBOSE (on both) + ROTATING (on the file).

    Example::
        logger = lab().with_profile("conspiracy_theorist").with_level("DEBUG").build(__name__)
        logger.debug("Raw response: %s", raw)
    """

    return (
        builder.with_output(Output.CONSOLE).with_output(Output.FILE)
        .with_feature(Feature.VERBOSE)
        .with_feature(Feature.ROTATING)
    )


CONSPIRACY_THEORIST_SPEC = ProfileSpec(member=ProfileType.CONSPIRATOR, recipe=conspiracy_theorist,
                                       summary="console + file + VERBOSE + ROTATING")
