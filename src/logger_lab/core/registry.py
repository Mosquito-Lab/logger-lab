"""
Central registry for experiments and profiles.

``EXPERIMENTS`` and ``PROFILES`` map `ExperimentType` and `ProfileType` enums members to their factory
callables.  Both dicts are populated via `register_experiment()` and `register_profile()`
not by direct dict mutation — so every entry is validated against its protocol at registration time.

Lookup is done through `get_experiment()` and `get_profile()`
so callers always receive a typed error on a miss rather than a ``KeyError``.
"""

import inspect
from typing import Callable, Protocol, runtime_checkable

from logger_lab.core.enums import ExperimentType, ProfileType, TheoryType
from logger_lab.logging_kernel.errors import (
    ExperimentNotFoundError, ExperimentRegistrationError,
    ProfileNotFoundError, ProfileRegistrationError,
)

##########################################################
# Protocols — typed contracts every factory must satisfy #
##########################################################

@runtime_checkable
class LabExperiment(Protocol):
    """Callable contract for lab experiment.

    Every experiment must be a callable that accepts an integer *level*
    and returns [logging.Handler] instances ready to be attached to any logger.

    The ``**kwargs`` signature allows experiments to accept optional
    keyword arguments (e.g. ``log_dir``, ``filename``) without breaking
    the protocol check.
    """

    def __call__(self, level: int, **kwargs: object) -> list: ...


@runtime_checkable
class LabProfile(Protocol):
    """Callable contract for lab profiles.

    Every profile must be a callable that accepts a logger *name* and
    an integer *level* and returns a fully configured `logging.Logger`.
    """

    def __call__(self, name: str, level: int) -> object: ...


##############################################################
# Registry dicts  (populated via register_* functions below) #
##############################################################

EXPERIMENTS : dict[ExperimentType, Callable] = {}
PROFILES    : dict[ProfileType   , Callable] = {}

# REGISTER HERE TO TEST A THEORY ( include the import)
from logger_lab.theories.timed_file_exp import timed_file_experiment

THEORIES    : dict[TheoryType    , Callable] = {
    TheoryType.TIMED_FILE: timed_file_experiment,
}

###############################################
# Registration helpers — validate then insert #
###############################################

def _validate_experiment(exp_enum: ExperimentType, lab_experiment: object) -> None:
    """
    Checks performed:

    * *experiment* must be callable.
    * *experiment* must accept at least one positional parameter (``level``).

    Args:
        exp_enum: The `ExperimentType` being registered.
        lab_experiment: The callable to validate.
    Raises:
        `ExperimentRegistrationError`:
            if *experiment* does not satisfy `LabExperiment`.
    """

    if not callable(lab_experiment):
        raise ExperimentRegistrationError(exp_enum, "lab experiment is not callable")

    # Checks the experiment's signature to see if the params are valid
    try:
        sig    = inspect.signature(lab_experiment)
        params = [
            p for p in sig.parameters.values()
            if p.kind not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
            and p.kind not in (
                inspect.Parameter.VAR_POSITIONAL,
                inspect.Parameter.VAR_KEYWORD,
            )
        ]

    except (ValueError, TypeError) as err:
        raise ExperimentRegistrationError(exp_enum, f"cannot inspect signature: {err}") from err

    if len(params) < 1:
        raise ExperimentRegistrationError(
            exp_enum,
            "lab experiment must accept at least one positional parameter ('level')"
        )


def _validate_profile(profile_enum: ProfileType, lab_profile: object) -> None:
    """
    Checks performed:

    * *profile* must be callable.
    * *profile* must accept at least two positional parameters (``name``, ``level``).

    Args:
        profile_enum: The `ProfileType` being registered.
        lab_profile: The callable to validate.
    Raises:
        `ProfileRegistrationError`:
            if *factory* does not satisfy :class:`ProfileFactory`.
    """

    if not callable(lab_profile):
        raise ProfileRegistrationError(profile_enum, "lab profile is not callable")

    # Checks the profile's signature to see if the params are valid
    try:
        sig    = inspect.signature(lab_profile)
        params = [
            p for p in sig.parameters.values()
            if p.kind not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
            and p.kind not in (
                inspect.Parameter.VAR_POSITIONAL,
                inspect.Parameter.VAR_KEYWORD,
            )
        ]

    except (ValueError, TypeError) as err:
        raise ProfileRegistrationError(profile_enum, f"cannot inspect signature: {err}") from err

    if len(params) < 2:
        raise ProfileRegistrationError(
            profile_enum,
            "lab profile must accept at least two positional parameters ('name', 'level')"
        )


def register_experiment(exp_enum: ExperimentType, lab_experiment: Callable) -> None:
    """
    Validate *experiment* and insert it into ``EXPERIMENTS``.

    Prefer this over direct dict mutation so validation always fires.

    Args:
        exp_enum: `ExperimentType` enum member to register under.
        lab_experiment: Callable satisfying `ExperimentFactory`.
    Raises:
        `ExperimentRegistrationError`:
            If *profile* fails protocol validation.
    Example::
        register_experiment(ExperimentType.STANDARD, standard_experiment)
    """

    _validate_experiment(exp_enum, lab_experiment)
    EXPERIMENTS[exp_enum] = lab_experiment


def register_profile(profile_enum: ProfileType, lab_profile: Callable) -> None:
    """
    Validate *profile* and insert it into ``PROFILES``.

    Args:
        profile_enum: `ProfileType` enum member to register under.
        lab_profile: Callable satisfying `ProfileFactory`.
    Raises:
        `ProfileRegistrationError`:
            If *profile* fails protocol validation.
    Example::
        register_profile(ProfileType.OBSERVER, observer)
    """

    _validate_profile(profile_enum, lab_profile)
    PROFILES[profile_enum] = lab_profile


##################
# Lookup helpers #
##################

# Returns an experiment
def get_experiment(experiment: ExperimentType) -> Callable:
    """
    Return the experiment registered for *experiment*.

    Args:
        experiment: A member of `ExperimentType` enum.
    Returns:
        The registered experiment.
    Raises:
        `ExperimentNotFoundError`:
            If *experiment* is not in the registry.
    """

    if experiment not in EXPERIMENTS:
        raise ExperimentNotFoundError(experiment)

    return EXPERIMENTS[experiment]


# Returns a profile
def get_profile(profile: ProfileType) -> Callable:
    """
    Return the profile registered for *profile*.

    Args:
        profile: A member of `ProfileType` enum.
    Returns:
        The registered profile.
    Raises:
        `ProfileNotFoundError`:
            If *profile* is not in the registry.
    """

    if profile not in PROFILES:
        raise ProfileNotFoundError(profile)

    return PROFILES[profile]


# EXPERIMENTAL
def get_theory(theory: TheoryType) -> Callable:
    """
    ONLY DO THIS IF YOU ACTUALLY MADE ONE.

    Args:
        theory: A member of `TheoryTpe` enum.
    Returns:
        The registered theory.
    Raises:
        Nothing! It's an untested theory for a reason
    """

    if theory not in THEORIES:
        print(f"Theory {theory} is not registered.")

    return THEORIES[theory]


# Registry population — imported here (after dicts + helpers are defined)
# to keep experiments and profiles free of any registry dependency.

# EXPERIMENTS
from logger_lab.experiments.standard      import standard_experiment
from logger_lab.experiments.verbose       import verbose_experiment
from logger_lab.experiments.minimalist    import minimalist_experiment
from logger_lab.experiments.file          import file_experiment
from logger_lab.experiments.rotating_file import rotating_file_experiment
from logger_lab.experiments.ai            import ai_experiment

# PROFILES
from logger_lab.profiles.observer            import observer
from logger_lab.profiles.investigator        import investigator
from logger_lab.profiles.conspiracy_theorist import conspiracy_theorist
from logger_lab.profiles.ai_agent            import ai_agent

# REGISTER EXPERIMENTS
for _exp_key, _exp_fn in [
    (ExperimentType.STANDARD,      standard_experiment),
    (ExperimentType.VERBOSE,       verbose_experiment),
    (ExperimentType.MINIMALIST,    minimalist_experiment),
    (ExperimentType.FILE,          file_experiment),
    (ExperimentType.ROTATING_FILE, rotating_file_experiment),
    (ExperimentType.AI,            ai_experiment),
]:
    register_experiment(_exp_key, _exp_fn)

# REGISTER PROFILES
for _prof_key, _prof_fn in [
    (ProfileType.OBSERVER,     observer),
    (ProfileType.INVESTIGATOR, investigator),
    (ProfileType.CONSPIRATOR,  conspiracy_theorist),
    (ProfileType.AGENT,        ai_agent),
]:
    register_profile(_prof_key, _prof_fn)
