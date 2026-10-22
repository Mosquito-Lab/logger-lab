import logging
from typing import TYPE_CHECKING

from logger_lab.logging_kernel.errors import (
    InvalidExperimentName, InvalidProfileName, InvalidTheoryName, InvalidLevelError,
)
from logger_lab.core.registry import ExperimentType, ProfileType

if TYPE_CHECKING:  # type-only: a runtime import here would join the registry import cycle (KN-3)
    from logger_lab.core.enums import TheoryType


# logger.DEBUG or 1
def normalize_level_name(level: int | str) -> int:
    """
    Coerce a level value to a :mod:`logging` integer constant.

    Accepts both string names (``"DEBUG"``, case-insensitive) and integer
    constants (``logging.DEBUG``).  Unknown string names fall back to
    ``logging.INFO`` — use `InvalidLevelError` at the call-site when strict validation is required.

    Args:
        level: Logging level as a string name or integer constant.
    Returns:
        An integer logging level.
    Example::
        normalize_level_name("debug")          # → 10  (logging.DEBUG)
        normalize_level_name(logging.WARNING)  # → 30
        normalize_level_name("NONSENSE")       # → 20  (logging.INFO, soft fallback)
    """

    if isinstance(level, str):
        return getattr(logging, level.upper(), logging.INFO)

    try:
        return level

    except InvalidLevelError:
        return logging.DEBUG


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


# Test case and example usage
def _test_case(normalizer, arg):
    """ Tests normalizer functionality """

    print(normalizer(arg))

if __name__ == "__main__":

    _test_case(normalize_level_name, "debug")
    _test_case(normalize_exp_name, "standard")
    _test_case(normalize_profile_name, "investigator")
