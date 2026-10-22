"""
Name resolution: turn whatever a caller passed (an enum member, a value string, a level
name or number) into the one form the builder works with — or raise a typed error.

The single owner of "what does this name mean" (Standards §2.6): the builder's ``with_*``
methods call these, so every entry point resolves names the same way.
"""

import logging
from typing import TYPE_CHECKING

from logger_lab.logging_kernel.errors import (
    InvalidExperimentName, InvalidProfileName, InvalidTheoryName, InvalidLevelError,
)

if TYPE_CHECKING:  # type-only: the enums are imported inside each function, because a module-level
    # import of logger_lab.core would load the registry, which imports this module (KN-3)
    from logger_lab.core.enums import ExperimentType, ProfileType, TheoryType


# logging.DEBUG, "debug" or a custom level
def normalize_level_name(level: int | str) -> int:
    """
    Coerce a level value to a :mod:`logging` integer level, or raise.

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
    """Return every level name logging knows — built-in, aliases and `addLevelName` ones — mapped to its number."""

    mapping = getattr(logging, "getLevelNamesMapping", None)  # Python 3.11+

    if mapping is not None:
        return mapping()

    return dict(logging._nameToLevel)  # Python 3.10: the same table getLevelNamesMapping() copies


# 'standard' or ExperimentType.STANDARD
def normalize_exp_name(experiment: "ExperimentType | str") -> "ExperimentType":
    """
    Coerce *experiment* to an `ExperimentType` enum.

    Accepts either the enum member itself or the string ``.value`` of the
    enum (e.g. ``"standard"``, ``"AI"``). String matching is case-insensitive.

    Args:
        experiment: An `ExperimentType` enum member or its string value.
    Returns:
        The matching `ExperimentType` member.
    Raises:
        `InvalidExperimentName` error:
            If *experiment* is a string that does not match any
            ``ExperimentType`` value.
    Example::
        normalize_exp_name("standard")          # → ExperimentType.STANDARD
        normalize_exp_name(ExperimentType.AI)   # → ExperimentType.AI (pass-through)
        normalize_exp_name("ghost")             # → raises InvalidExperimentName
    """

    # Lazy loaded so no runtime funny business
    from logger_lab.core.enums import ExperimentType

    if isinstance(experiment, ExperimentType):
        return experiment

    if not isinstance(experiment, str):
        raise InvalidExperimentName(experiment)

    try:
        return ExperimentType(experiment.upper())

    except ValueError:
        raise InvalidExperimentName(experiment)


# 'conspiracy_theorist' or ExperimentType.CONSPIRACY_THEORIST
def normalize_profile_name(profile: "ProfileType | str") -> "ProfileType":
    """
    Coerce *profile* to a `ProfileType` enum.

    Accepts either the enum member itself or the string ``.value`` of the
    enum (e.g. ``"investigator"``).  String matching is case-insensitive.

    Args:
        profile: A `ProfileType` enum member or its string value.
    Returns:
        The matching `ProfileType` member.
    Raises:
        `InvalidProfileName` error:
            If *profile* is a string that does not match any
            ``ProfileType`` value.
    Example::
        normalize_profile_name("observer")           # → ProfileType.OBSERVER
        normalize_profile_name(ProfileType.AGENT)    # → ProfileType.AGENT (pass-through)
        normalize_profile_name("ghost")              # → raises InvalidProfileName
    """

    # Lazy loaded so no runtime funny business
    from logger_lab.core.enums import ProfileType

    if isinstance(profile, ProfileType):
        return profile

    if not isinstance(profile, str):
        raise InvalidProfileName(profile)

    try:
        return ProfileType(profile.upper())

    except ValueError:
        raise InvalidProfileName(profile)


# 'timed_file' or TheoryType.TIMED_FILE
def normalize_theory_name(theory: "TheoryType | str") -> "TheoryType":
    """
    Coerce *theory* to a `TheoryType` enum.

    Accepts either the enum member itself or the string ``.value`` of the
    enum (e.g. ``"TIMED_FILE"``).  String matching is case-insensitive.

    Args:
        theory: A `TheoryType` enum member or its string value.
    Returns:
        The matching `TheoryType` member.
    Raises:
        `InvalidTheoryName` error:
            If *theory* is a string that does not match any
            ``TheoryType`` value.
    Example::
        normalize_theory_name("timed_file")         # → TheoryType.TIMED_FILE
        normalize_theory_name(TheoryType.TRACE)     # → TheoryType.TRACE (pass-through)
        normalize_theory_name("ghost")              # → raises InvalidTheoryName
    """

    # Lazy loaded so no runtime funny business
    from logger_lab.core.enums import TheoryType

    if isinstance(theory, TheoryType):
        return theory

    if not isinstance(theory, str):
        raise InvalidTheoryName(theory)

    try:
        return TheoryType(theory.upper())

    except ValueError:
        raise InvalidTheoryName(theory)

