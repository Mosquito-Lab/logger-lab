"""
Central registry for experiments, profiles, and theories.

``EXPERIMENTS``, ``PROFILES`` and ``THEORIES`` map their enum members to factory
callables.  All three are populated via `register_experiment()`, `register_profile()`
and `register_theory()` — not by direct dict mutation — so every entry is validated
at registration time.

Two more dicts carry the composition rules the builder enforces:

* ``CHANNELS`` — the `Channel` (console, file, JSON) each experiment and theory owns.
  A logger holds at most one experiment per channel.
* ``PROFILE_EXPERIMENTS`` — the experiments each profile is built from, so a profile
  can be checked against whatever else is queued.

Lookup is done through `get_experiment()`, `get_profile()`, `get_theory()` and
`get_channel()` so callers always receive a typed error on a miss rather than a ``KeyError``.
"""

import inspect
from typing import Callable, Iterable, Protocol, runtime_checkable

from logger_lab.core.enums import Channel, ExperimentType, ProfileType, TheoryType
from logger_lab.logging_kernel.errors import (
    ExperimentNotFoundError, ExperimentRegistrationError,
    ProfileNotFoundError, ProfileRegistrationError,
    TheoryNotFoundError,
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
    keyword arguments (e.g. the ``log_dir``, ``filename`` file args) without
    breaking the protocol check. Console experiments must still accept and
    ignore them, because the builder forwards the same args to every experiment.
    """

    def __call__(self, level: int, **kwargs: object) -> list: ...


@runtime_checkable
class LabProfile(Protocol):
    """Callable contract for lab profiles.

    Every profile must be a callable that accepts a logger *name* and
    an integer *level* and returns a fully configured `logging.Logger`.

    The ``**kwargs`` signature carries the file args from
    `LabBuilder.with_file_args()` through to the profile's experiments.
    """

    def __call__(self, name: str, level: int, **kwargs: object) -> object: ...


##############################################################
# Registry dicts  (populated via register_* functions below) #
##############################################################

EXPERIMENTS         : dict[ExperimentType, Callable] = {}
PROFILES            : dict[ProfileType   , Callable] = {}
THEORIES            : dict[TheoryType    , Callable] = {}
CHANNELS            : dict[ExperimentType | TheoryType, Channel] = {}
PROFILE_EXPERIMENTS : dict[ProfileType, tuple[ExperimentType, ...]] = {}

###############################################
# Registration helpers — validate then insert #
###############################################

def _validate_experiment(exp_enum: ExperimentType | TheoryType, lab_experiment: object) -> None:
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


def register_experiment(exp_enum: ExperimentType, lab_experiment: Callable, channel: Channel) -> None:
    """
    Validate *experiment* and insert it into ``EXPERIMENTS``, recording its *channel*.

    Prefer this over direct dict mutation so validation always fires.

    Args:
        exp_enum: `ExperimentType` enum member to register under.
        lab_experiment: Callable satisfying `LabExperiment`.
        channel: The `Channel` the experiment's handler writes to.
    Raises:
        `ExperimentRegistrationError`:
            If *lab_experiment* fails protocol validation.
    Example::
        register_experiment(ExperimentType.STANDARD, standard_experiment, Channel.CONSOLE)
    """

    _validate_experiment(exp_enum, lab_experiment)
    EXPERIMENTS[exp_enum] = lab_experiment
    CHANNELS[exp_enum] = channel


def register_profile(
    profile_enum: ProfileType,
    lab_profile: Callable,
    experiments: tuple[Callable, ...],
) -> None:
    """
    Validate *profile* and its declared *experiments*, then insert it into ``PROFILES``.

    *experiments* is the same tuple the profile function builds from (its module's
    ``*_EXPERIMENTS`` constant), so the builder can check a profile against anything
    queued on top of it.  Each factory must already be a registered experiment, and
    no two may share a channel — a clashing profile fails here, at import time.

    Args:
        profile_enum: `ProfileType` enum member to register under.
        lab_profile: Callable satisfying `LabProfile`.
        experiments: The experiment factories the profile is built from, in order.
    Raises:
        `ProfileRegistrationError`:
            If *lab_profile* fails protocol validation, an experiment is not
            registered, or two experiments share a channel.
    Example::
        register_profile(ProfileType.OBSERVER, observer, OBSERVER_EXPERIMENTS)
    """

    _validate_profile(profile_enum, lab_profile)

    experiment_types = {factory: exp_enum for exp_enum, factory in EXPERIMENTS.items()}
    unknown = [f.__name__ for f in experiments if f not in experiment_types]

    if unknown:
        raise ProfileRegistrationError(profile_enum, f"unregistered experiments: {', '.join(unknown)}")

    declared = tuple(experiment_types[factory] for factory in experiments)
    clash = find_channel_clash(declared)

    if clash is not None:
        first, second, channel = clash
        raise ProfileRegistrationError(
            profile_enum,
            f"'{first.value}' and '{second.value}' both write to the {channel.value} channel"
        )

    PROFILES[profile_enum] = lab_profile
    PROFILE_EXPERIMENTS[profile_enum] = declared


def register_theory(theory_enum: TheoryType, lab_theory: Callable, channel: Channel) -> None:
    """
    Validate a working theory and insert it into ``THEORIES``, recording its *channel*.

    Only register a theory once its factory actually works (the *trial* stage);
    an unregistered `TheoryType` is a placeholder and raises `TheoryNotFoundError`
    when selected.  Validation is the same as for experiments.

    Args:
        theory_enum: `TheoryType` enum member to register under.
        lab_theory: Callable satisfying `LabExperiment`.
        channel: The `Channel` the theory's handler writes to.
    Raises:
        `ExperimentRegistrationError`:
            If *lab_theory* fails protocol validation.
    Example::
        register_theory(TheoryType.TIMED_FILE, timed_file_experiment, Channel.FILE)
    """

    _validate_experiment(theory_enum, lab_theory)
    THEORIES[theory_enum] = lab_theory
    CHANNELS[theory_enum] = channel


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


# Returns a profile's declared experiments
def get_profile_experiments(profile: ProfileType) -> tuple[ExperimentType, ...]:
    """
    Return the experiments *profile* is built from, in order.

    Args:
        profile: A member of `ProfileType` enum.
    Returns:
        The profile's `ExperimentType` members, as declared at registration.
    Raises:
        `ProfileNotFoundError`:
            If *profile* is not in the registry.
    Example::
        get_profile_experiments(ProfileType.INVESTIGATOR)
        # → (ExperimentType.STANDARD, ExperimentType.FILE)
    """

    if profile not in PROFILE_EXPERIMENTS:
        raise ProfileNotFoundError(profile)

    return PROFILE_EXPERIMENTS[profile]


# Returns a theory
def get_theory(theory: TheoryType) -> Callable:
    """
    Return the theory registered for *theory*.

    Args:
        theory: A member of `TheoryType` enum.
    Returns:
        The registered theory.
    Raises:
        `TheoryNotFoundError`:
            If *theory* is still a placeholder (nothing registered).
    """

    if theory not in THEORIES:
        raise TheoryNotFoundError(theory)

    return THEORIES[theory]


# Returns the channel an experiment or theory writes to
def get_channel(entry: ExperimentType | TheoryType) -> Channel:
    """
    Return the `Channel` *entry* writes to.

    Args:
        entry: An `ExperimentType` or `TheoryType` member.
    Returns:
        The channel recorded when *entry* was registered.
    Raises:
        `ExperimentNotFoundError` / `TheoryNotFoundError`:
            If *entry* is not registered.
    """

    if entry not in CHANNELS:
        if isinstance(entry, TheoryType):
            raise TheoryNotFoundError(entry)

        raise ExperimentNotFoundError(entry)

    return CHANNELS[entry]


def find_channel_clash(
    entries: Iterable[ExperimentType | TheoryType],
) -> tuple[ExperimentType | TheoryType, ExperimentType | TheoryType, Channel] | None:
    """
    Return the first pair of *entries* that write to the same channel, or ``None``.

    The single home of the one-experiment-per-channel rule — `register_profile()`
    and `LabBuilder.plan()` both ask it.  *entries* should already be free of
    duplicates; the same experiment twice is a duplicate, not a clash.

    Args:
        entries: Experiments and theories, in the order they would be built.
    Returns:
        ``(first, second, channel)`` for the first clash found, else ``None``.
    Raises:
        `ExperimentNotFoundError` / `TheoryNotFoundError`:
            If an entry is not registered.
    Example::
        find_channel_clash([ExperimentType.STANDARD, ExperimentType.MINIMALIST])
        # → (ExperimentType.STANDARD, ExperimentType.MINIMALIST, Channel.CONSOLE)
    """

    claimed: dict[Channel, ExperimentType | TheoryType] = {}

    for entry in entries:
        channel = get_channel(entry)

        if channel in claimed:
            return claimed[channel], entry, channel

        claimed[channel] = entry

    return None


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
from logger_lab.profiles.observer            import observer, OBSERVER_EXPERIMENTS
from logger_lab.profiles.investigator        import investigator, INVESTIGATOR_EXPERIMENTS
from logger_lab.profiles.conspiracy_theorist import conspiracy_theorist, CONSPIRACY_THEORIST_EXPERIMENTS
from logger_lab.profiles.ai_agent            import ai_agent, AI_AGENT_EXPERIMENTS

# REGISTER EXPERIMENTS
for _exp_key, _exp_fn, _channel in [
    (ExperimentType.STANDARD,      standard_experiment,      Channel.CONSOLE),
    (ExperimentType.VERBOSE,       verbose_experiment,       Channel.CONSOLE),
    (ExperimentType.MINIMALIST,    minimalist_experiment,    Channel.CONSOLE),
    (ExperimentType.FILE,          file_experiment,          Channel.FILE),
    (ExperimentType.ROTATING_FILE, rotating_file_experiment, Channel.FILE),
    (ExperimentType.AI,            ai_experiment,            Channel.JSON),
]:
    register_experiment(_exp_key, _exp_fn, _channel)

# REGISTER PROFILES (after experiments — each profile's experiments must already be registered)
for _prof_key, _prof_fn, _prof_exps in [
    (ProfileType.OBSERVER,     observer,            OBSERVER_EXPERIMENTS),
    (ProfileType.INVESTIGATOR, investigator,        INVESTIGATOR_EXPERIMENTS),
    (ProfileType.CONSPIRATOR,  conspiracy_theorist, CONSPIRACY_THEORIST_EXPERIMENTS),
    (ProfileType.AGENT,        ai_agent,            AI_AGENT_EXPERIMENTS),
]:
    register_profile(_prof_key, _prof_fn, _prof_exps)

# REGISTER THEORIES — add a theory here once its factory works (the trial stage):
#     from logger_lab.theories.timed_file_exp import timed_file_experiment
#     register_theory(TheoryType.TIMED_FILE, timed_file_experiment, Channel.FILE)
# None have left the placeholder stage yet, so THEORIES starts empty.
