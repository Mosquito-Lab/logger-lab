"""Registration validates factories, profile compositions and theories; lookups raise typed errors."""

import logging

import pytest

from logger_lab import ExperimentType, ProfileType, TheoryNotFoundError, TheoryType, lab
from logger_lab.core import registry
from logger_lab.core.registry import (
    PROFILE_EXPERIMENTS, get_profile, get_theory, register_experiment, register_profile, register_theory,
)
from logger_lab.core.enums import Channel
from logger_lab.experiments import (
    async_experiment, file_experiment, minimalist_experiment, rotating_file_experiment, standard_experiment,
)
from logger_lab.logging_kernel import ExperimentRegistrationError, ProfileRegistrationError
from logger_lab.profiles import observer


def test_profile_with_clashing_experiments_is_rejected():
    """A profile whose own experiments share a channel fails at registration."""

    with pytest.raises(ProfileRegistrationError, match="FILE.*ROTATING|both write to the FILE channel"):
        register_profile(ProfileType.OBSERVER, observer, (file_experiment, rotating_file_experiment))

    with pytest.raises(ProfileRegistrationError, match="CONSOLE"):
        register_profile(ProfileType.OBSERVER, observer, (standard_experiment, minimalist_experiment))


def test_profile_with_unregistered_experiment_is_rejected():
    """Every factory a profile declares must be a registered experiment."""

    def stray_experiment(level: int, **kwargs: object) -> list:
        """Not registered anywhere."""

        return []

    with pytest.raises(ProfileRegistrationError, match="stray_experiment"):
        register_profile(ProfileType.OBSERVER, observer, (stray_experiment,))


def handler_shape(logger: logging.Logger) -> list:
    """Handler types on *logger*, with a dispatcher's targets nested inside it."""

    return [(type(h), [type(t) for t in getattr(h, "targets", ())]) for h in logger.handlers]


@pytest.mark.parametrize("profile", list(ProfileType))
def test_profile_function_matches_its_declared_experiments(profile):
    """Calling a profile directly builds exactly what the builder builds from its declared experiments."""

    direct = get_profile(profile)(f"direct.{profile.value}", logging.DEBUG)
    built = lab().with_profile(profile).with_level("DEBUG").build(f"built.{profile.value}")

    assert handler_shape(direct) == handler_shape(built)
    assert lab().with_profile(profile).plan() == list(PROFILE_EXPERIMENTS[profile])


def test_dispatch_channel_and_dispatcher_mark_must_agree():
    """An ordinary factory can't take the DISPATCH channel, and a dispatcher can't take another one."""

    with pytest.raises(ExperimentRegistrationError, match="DISPATCH"):
        register_experiment(ExperimentType.STANDARD, standard_experiment, Channel.DISPATCH)

    with pytest.raises(ExperimentRegistrationError, match="DISPATCH"):
        register_experiment(ExperimentType.ASYNC, async_experiment, Channel.CONSOLE)


def test_placeholder_theory_raises_typed_error():
    """An unregistered theory is a placeholder, reported as `TheoryNotFoundError`."""

    with pytest.raises(TheoryNotFoundError, match="'TRACE' is still a placeholder"):
        get_theory(TheoryType.TRACE)


def test_register_theory_validates_and_records_channel(monkeypatch):
    """A working theory registers with its channel and can then be built."""

    monkeypatch.setattr(registry, "THEORIES", {})
    monkeypatch.setattr(registry, "CHANNELS", dict(registry.CHANNELS))

    def trace_experiment(level: int, **kwargs: object) -> list:
        """A stand-in theory with one console handler."""

        return [logging.StreamHandler()]

    register_theory(TheoryType.TRACE, trace_experiment, Channel.CONSOLE)

    assert get_theory(TheoryType.TRACE) is trace_experiment
    assert registry.CHANNELS[TheoryType.TRACE] is Channel.CONSOLE

    with pytest.raises(ExperimentRegistrationError):
        register_theory(TheoryType.SEC, "not callable", Channel.FILE)  # pyrefly: ignore[bad-argument-type]


def test_registered_theory_builds_with_its_options(monkeypatch):
    """`with_theory()` options reach only that theory's factory, on top of the file args."""

    from logger_lab import lab

    seen: dict[str, object] = {}

    def timed_experiment(level: int, **kwargs: object) -> list:
        """Records what it was called with."""

        seen.update(kwargs)

        return []

    monkeypatch.setattr(registry, "THEORIES", {TheoryType.TIMED_FILE: timed_experiment})
    monkeypatch.setattr(registry, "CHANNELS", {**registry.CHANNELS, TheoryType.TIMED_FILE: Channel.FILE})

    lab().with_theory("timed_file", when="midnight").with_file_args("t").build("timed")

    assert seen["when"] == "midnight" and seen["log_dir"] == "t"
