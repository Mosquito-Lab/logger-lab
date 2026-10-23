"""
AI Agent profile: structured JSON on the console, for machines to read.

One console with the ``JSON`` format: every record is one JSON object (Mosquito Lab Logging
Standard v1.2), ready for LLM APIs, log aggregators and pipelines. Pair with `log_event` to
attach ``event``, ``context`` and ``tags``.
"""

from typing import TYPE_CHECKING

from logger_lab.core.enums import Format, Output, ProfileType
from logger_lab.core.specs import ProfileSpec

if TYPE_CHECKING:  # type-only: the builder imports the registry, which imports this module
    from logger_lab.core.builder import LabBuilder


def ai_agent(builder: "LabBuilder") -> "LabBuilder":
    """
    Console + JSON.

    Example::
        logger = lab().with_profile("ai_agent").build(__name__)
        log_event(logger, logging.INFO, "Tool call dispatched", event="tool_dispatch",
                  context={"tool": "web_search"})
    """

    return builder.with_output(Output.CONSOLE).with_format(Format.JSON, on=Output.CONSOLE)


AI_AGENT_SPEC = ProfileSpec(member=ProfileType.AGENT, recipe=ai_agent, summary="console + JSON")
