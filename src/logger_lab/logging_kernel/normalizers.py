"""
Name resolution: turn whatever a caller passed (an enum member, a value string, a level
name or number) into the one form the builder works with. Anything else raises a typed error.

The single owner of "what does this name mean" (Standards §2.6): every builder method
resolves names through here, so all four kinds, profiles and theories behave the same.
"""

import logging
from enum import Enum
from typing import TypeVar

from logger_lab.logging_kernel.errors import InvalidLevelError, InvalidNameError

E = TypeVar("E", bound=Enum)  # Any of logger-lab's name enums


#########
# Names #
#########

def normalize_name(enum_type: type[E], value: E | str, kind: str) -> E:
    """
    Coerce *value* to a member of *enum_type*, or raise.

    Accepts the member itself or its value string, case-insensitively. The member's
    *name* as a string is not an alias when it differs from the value.

    Args:
        enum_type: The enum to resolve into, e.g. `Output`.
        value:     A member or a value string.
        kind:      The kind's label for the error message, e.g. ``"output"``.
    Returns:
        The matching member.
    Raises:
        `InvalidNameError`: If *value* is neither a member nor a value string.
    Example::
        normalize_name(Output, "file", "output")      # → Output.FILE
        normalize_name(Output, "screen", "output")    # → raises InvalidNameError
    """

    if isinstance(value, enum_type):
        return value

    if isinstance(value, str):
        try:
            return enum_type(value.upper())

        except ValueError:
            pass

    raise InvalidNameError(kind, value, [member.value for member in enum_type])


##########
# Levels #
##########

def normalize_level_name(level: int | str) -> int:
    """
    Coerce a level value to a `logging` integer level, or raise.

    Accepts level names, case-insensitive (``"debug"``, ``"WARNING"``, the stdlib
    aliases ``"WARN"``/``"FATAL"``, and custom names added with `logging.addLevelName`),
    and any integer ``0`` or above, since the stdlib allows custom numeric levels.

    Args:
        level: Logging level as a name or an integer.
    Returns:
        An integer logging level.
    Raises:
        `InvalidLevelError`: For an unknown name, a negative number, or any other type
            (``bool``, ``float``, ``None``, …).
    Example::
        normalize_level_name("debug")          # → 10  (logging.DEBUG)
        normalize_level_name(logging.WARNING)  # → 30
        normalize_level_name("DEBG")           # → raises InvalidLevelError
    """

    if isinstance(level, int) and not isinstance(level, bool):
        if level >= 0:
            return level

    elif isinstance(level, str):
        resolved = level_names().get(level.upper())

        if resolved is not None:
            return resolved

    raise InvalidLevelError(level)


def level_names() -> dict[str, int]:
    """Return every level name logging knows, mapped to its number: built-in names, aliases and `addLevelName` ones."""

    mapping = getattr(logging, "getLevelNamesMapping", None)  # Python 3.11+

    if mapping is not None:
        return mapping()

    return dict(logging._nameToLevel)  # Python 3.10: the same table getLevelNamesMapping() copies
