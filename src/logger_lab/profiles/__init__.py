"""
Profiles — named combinations of experiments, plus `build_profile` for writing your own.

``observer``, ``investigator``, ``conspiracy_theorist``, ``ai_agent``, ``gui``.
"""

from logger_lab.profiles.base               import build_profile
from logger_lab.profiles.ai_agent            import ai_agent
from logger_lab.profiles.conspiracy_theorist import conspiracy_theorist
from logger_lab.profiles.gui                 import gui
from logger_lab.profiles.investigator        import investigator
from logger_lab.profiles.observer            import observer

__all__ = [
    "build_profile",
    "observer",
    "investigator",
    "conspiracy_theorist",
    "ai_agent",
    "gui",
]
