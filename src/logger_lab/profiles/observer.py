"""
Observer profile: low-noise console output, with the level and message and nothing else.

One console with the ``MINIMAL`` detail feature. The level is ``INFO`` like every logger;
raise it with ``.with_level("WARNING")`` to hear only what matters.
"""

from typing import TYPE_CHECKING

from logger_lab.core.enums import Feature, Output, ProfileType
from logger_lab.core.specs import ProfileSpec

if TYPE_CHECKING:  # type-only: the builder imports the registry, which imports this module
    from logger_lab.core.builder import LabBuilder


def observer(builder: "LabBuilder") -> "LabBuilder":
    """
    Console + MINIMAL.

    Example::
        logger = lab().with_profile("observer").with_level("WARNING").build(__name__)
        logger.warning("Disk usage above 90%")   # → WARNING  Disk usage above 90%
    """

    return builder.with_output(Output.CONSOLE).with_feature(Feature.MINIMAL, on=Output.CONSOLE)


OBSERVER_SPEC = ProfileSpec(member=ProfileType.OBSERVER, recipe=observer, summary="console + MINIMAL")
