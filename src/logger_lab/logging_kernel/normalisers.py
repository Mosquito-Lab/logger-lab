import logging

from logger_lab.logging_kernel.errors import InvalidExperimentName, InvalidProfileName, InvalidLevelError
from logger_lab.core.registry import ExperimentType, ProfileType


# logger.DEBUG or 1
def normalise_level_name(level: int | str) -> int:
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
        normalise_level_name("debug")          # → 10  (logging.DEBUG)
        normalise_level_name(logging.WARNING)  # → 30
        normalise_level_name("NONSENSE")       # → 20  (logging.INFO, soft fallback)
    """

    if isinstance(level, str):
        return getattr(logging, level.upper(), logging.INFO)

    try:
        return level

    except InvalidLevelError:
        return logging.DEBUG


# 'standard' or ExperimentType.STANDARD
def normalise_exp_name(experiment: "ExperimentType | str") -> "ExperimentType":
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
        normalise_exp_name("standard")          # → ExperimentType.STANDARD
        normalise_exp_name(ExperimentType.AI)   # → ExperimentType.AI (pass-through)
        normalise_exp_name("ghost")             # → raises InvalidExperimentName
    """

    # Lazy loaded so no runtime funny business
    from logger_lab.core.enums import ExperimentType

    if isinstance(experiment, ExperimentType):
        return experiment

    try:
        return ExperimentType(experiment.upper())

    except ValueError:
        raise InvalidExperimentName(experiment)


# 'conspiracy_theorist' or ExperimentType.CONSPIRACY_THEORIST
def normalise_profile_name(profile: "ProfileType | str") -> "ProfileType":
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
        normalise_profile_name("observer")           # → ProfileType.OBSERVER
        normalise_profile_name(ProfileType.AGENT)    # → ProfileType.AGENT (pass-through)
        normalise_profile_name("ghost")              # → raises InvalidProfileName
    """

    # Lazy loaded so no runtime funny business
    from logger_lab.core.enums import ProfileType

    if isinstance(profile, ProfileType):
        return profile

    try:
        return ProfileType(profile.upper())

    except ValueError:
        raise InvalidProfileName(profile)


# Test case and example usage
def _test_case(normaliser, arg):
    """ Tests normaliser functionality """

    print(normaliser(arg))

if __name__ == "__main__":

    _test_case(normalise_level_name, "debug")
    _test_case(normalise_exp_name, "standard")
    _test_case(normalise_profile_name, "investigator")
