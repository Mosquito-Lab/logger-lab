"""
The names logger-lab knows: experiments, profiles, theories, and the channels experiments write to.

Select a member by the member itself (``ExperimentType.ROTATING_FILE``) or by its **value**
string, case-insensitively (``"ROTATING"``).  A member's *name* may differ from its value
(``ROTATING_FILE``/``"ROTATING"``, ``AGENT``/``"AI_AGENT"``, ``CONSPIRATOR``/``"CONSPIRACY_THEORIST"``);
the name as a string is not an alias.
"""

from enum import Enum


class ExperimentType(Enum):
    """Registered experiments — one logging behavior each."""

    AI            = "AI"
    ASYNC         = "ASYNC"
    FILE          = "FILE"
    VERBOSE       = "VERBOSE"
    STANDARD      = "STANDARD"
    MINIMALIST    = "MINIMALIST"
    RELAY         = "RELAY"
    ROTATING_FILE = "ROTATING"


class ProfileType(Enum):
    """Registered profiles — named combinations of experiments."""

    AGENT        = "AI_AGENT"
    GUI          = "GUI"
    OBSERVER     = "OBSERVER"
    INVESTIGATOR = "INVESTIGATOR"
    CONSPIRATOR  = "CONSPIRACY_THEORIST"


class Channel(Enum):
    """The output an experiment owns — a logger holds at most one experiment per channel."""

    CONSOLE  = "CONSOLE"
    FILE     = "FILE"
    JSON     = "JSON"
    LIVE     = "LIVE"      # Records handed to subscriber callbacks (relay)
    DISPATCH = "DISPATCH"  # Not an output: how records reach the others (async)


class TheoryType(Enum):
    """Theories — experiments still being researched (placeholders until registered)."""

    DB          = "DB"
    HTTP        = "HTTP"
    PERFORMANCE = "PERFORMANCE"
    SEC         = "SEC"
    TIMED_FILE  = "TIMED_FILE"
    TRACE       = "TRACE"
