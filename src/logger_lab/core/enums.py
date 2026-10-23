"""
The names logger-lab knows: the four kinds of building block, profiles and theories.

| Kind     | Enum       | Builder method      | What it is                                   |
| -------- | ---------- | ------------------- | -------------------------------------------- |
| Output   | `Output`   | ``with_output()``   | Where feedback goes                          |
| Feature  | `Feature`  | ``with_feature()``  | Extra behavior on an output                  |
| Format   | `Format`   | ``with_format()``   | How a record looks                           |
| Catalyst | `Catalyst` | ``with_catalyst()`` | How every record flows to the outputs        |

Two more enums name option values of the ``TIMED`` feature: `Unit` and `Day`.

Select a member by the member itself (``Output.FILE``) or by its value string,
case-insensitively (``"file"``). A member's *name* may differ from its value
(``ProfileType.AGENT`` / ``"AI_AGENT"``, ``ProfileType.CONSPIRATOR`` / ``"CONSPIRACY_THEORIST"``);
the name as a string is not an alias.
"""

from enum import Enum


def value_of(member: Enum) -> str:
    """
    A member's value string, in one typed place.

    PyCharm types ``Enum.value`` as a function, and pyrefly rejects a typed override of it,
    so the value is read with `getattr` (typed ``Any``) and returned as ``str``.
    """

    return str(getattr(member, "value"))


class Kind(Enum):
    """The four kinds of building block."""

    OUTPUT   = "OUTPUT"
    FEATURE  = "FEATURE"
    FORMAT   = "FORMAT"
    CATALYST = "CATALYST"


class Output(Enum):
    """Where feedback goes. A logger holds at most one output of each."""

    CONSOLE = "CONSOLE"  # Rich console (or plain/JSON with a format)
    FILE    = "FILE"     # One shared log file per path
    RELAY   = "RELAY"    # Records handed to subscriber callbacks


class Feature(Enum):
    """Extra behavior on an output."""

    MINIMAL  = "MINIMAL"   # Less detail: level and message (console, file)
    VERBOSE  = "VERBOSE"   # More detail: logger name and module.func:line (console, file)
    ROTATING = "ROTATING"  # Roll the file over at a size (file)
    TIMED    = "TIMED"     # Roll the file over on a schedule (file)


class Format(Enum):
    """How a record looks."""

    RICH = "RICH"  # Rich rendering: console only, and the console's default
    TEXT = "TEXT"  # Plain text lines: the file's default
    JSON = "JSON"  # Mosquito Lab Logging Standard v1.2, one object per line


class Catalyst(Enum):
    """How every record flows to the outputs."""

    ASYNC = "ASYNC"  # Queue records; one worker thread writes them


class Unit(Enum):
    """The unit of a ``TIMED`` schedule (``unit=``). As a string, the plural works too ("hours")."""

    MINUTE = "MINUTE"
    HOUR   = "HOUR"
    DAY    = "DAY"
    WEEK   = "WEEK"
    MONTH  = "MONTH"


class Day(Enum):
    """The day a weekly ``TIMED`` schedule starts on (``day=``)."""

    MONDAY    = "MONDAY"
    TUESDAY   = "TUESDAY"
    WEDNESDAY = "WEDNESDAY"
    THURSDAY  = "THURSDAY"
    FRIDAY    = "FRIDAY"
    SATURDAY  = "SATURDAY"
    SUNDAY    = "SUNDAY"


class ProfileType(Enum):
    """Registered profiles: common compositions of the four kinds."""

    AGENT        = "AI_AGENT"
    GUI          = "GUI"
    OBSERVER     = "OBSERVER"
    INVESTIGATOR = "INVESTIGATOR"
    CONSPIRATOR  = "CONSPIRACY_THEORIST"


class TheoryType(Enum):
    """Theories: building blocks still being researched (placeholders until registered)."""

    DB          = "DB"
    HTTP        = "HTTP"
    LIFECYCLE   = "LIFECYCLE"
    PERFORMANCE = "PERFORMANCE"
    PROCESS     = "PROCESS"
    SEC         = "SEC"
    THROTTLE    = "THROTTLE"
    TRACE       = "TRACE"
