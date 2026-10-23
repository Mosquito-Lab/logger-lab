"""
Profiles: the common compositions, each a recipe of builder calls.

| Profile                 | Composition                          |
| ----------------------- | ------------------------------------ |
| ``observer``            | console + MINIMAL                    |
| ``investigator``        | console + file                       |
| ``conspiracy_theorist`` | console + file + VERBOSE + ROTATING  |
| ``ai_agent``            | console + JSON                       |
| ``gui``                 | file + ROTATING + relay + ASYNC      |

Start from one with ``lab().with_profile(name)``, then add or configure on top. A recipe
only calls the builder, so a profile obeys every composition rule. The tests plan every
profile, so a recipe that breaks a rule fails there. A recipe pins its features and formats
with ``on=`` wherever an output added later could also take them. For example,
``ai_agent``'s JSON belongs to the console, not to a file added on top.
"""

from logger_lab.profiles.ai_agent import AI_AGENT_SPEC
from logger_lab.profiles.conspiracy_theorist import CONSPIRACY_THEORIST_SPEC
from logger_lab.profiles.gui import GUI_SPEC
from logger_lab.profiles.investigator import INVESTIGATOR_SPEC
from logger_lab.profiles.observer import OBSERVER_SPEC

PROFILE_SPECS = (OBSERVER_SPEC, INVESTIGATOR_SPEC, CONSPIRACY_THEORIST_SPEC, AI_AGENT_SPEC, GUI_SPEC)

__all__ = [
    "PROFILE_SPECS",
    "OBSERVER_SPEC",
    "INVESTIGATOR_SPEC",
    "CONSPIRACY_THEORIST_SPEC",
    "AI_AGENT_SPEC",
    "GUI_SPEC",
]
