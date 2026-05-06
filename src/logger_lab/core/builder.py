from logging import INFO, Logger, getLogger

from logger_lab.core.enums import ExperimentType, ProfileType, TheoryType
from logger_lab.core.registry import get_experiment, get_profile, get_theory
from logger_lab.logging_kernel.errors import BuilderError
from logger_lab.logging_kernel.handlers import (
    clear_handlers,
    normalise_exp_name, normalise_level_name, normalise_profile_name,
)


class LabBuilder:
    """
    Fluent builder for composing logger-lab configurations.

    Each ``with_*`` method mutates the builder and returns ``self`` so
    calls can be chained.  Call `build()` last to materialise the
    configured `logging.Logger`.

    At least one experiment or profile must be queued before calling
    `build`; an empty builder raises `BuilderError`.
    """

    def __init__(self) -> None:
        self._experiments: list[ExperimentType | TheoryType] = []
        self._profile: ProfileType | None = None
        self._level: int = INFO

    def with_experiment(self, experiment: ExperimentType | str | TheoryType) -> "LabBuilder":
        """
        Queue an experiment to be applied during `build()`.

        Accepts either an `ExperimentType` enum member or its string alias
        (e.g. ``"standard"``, ``"AI"``). Experiments are applied in the order
        they are queued, after the profile (if any).

        Args:
            experiment: Experiment identifier — enum member or string alias.
        Returns:
            ``self``, for method chaining.
        Raises:
            `InvalidExperimentName`:
                If *experiment* is a string that does not match any
                registered experiment.
        Example::
            lab().with_experiment("standard").with_experiment(ExperimentType.AI)
        """

        if type(experiment) is TheoryType:
            self._experiments.append(experiment)

        else:
            self._experiments.append(normalise_exp_name(experiment))

        return self

    def with_profile(self, profile: ProfileType | str) -> "LabBuilder":
        """
        Use a named profile instead of (or alongside) individual experiments.

        When a profile is set it is applied *before* any experiments
        queued via `with_experiment()`. Only one profile may be
        set; calling this again replaces the previous value.

        Args:
            profile: Profile identifier — enum member or string alias.
        Returns:
            ``self``, for method chaining.
        Raises:
            `InvalidProfileName`:
                If *profile* is a string that does not match any
                registered profile.
        Example::
            lab().with_profile("investigator").build(__name__)
        """

        self._profile = normalise_profile_name(profile)

        return self

    def with_level(self, level: int | str) -> "LabBuilder":
        """
        Set the logging level applied to the logger and all handlers.

        Accepts both string names (``"DEBUG"``, case-insensitive) and
        integer constants (``logging.DEBUG``). Unknown strings fall
        back to ``logging.INFO`` — use `InvalidLevelError`
        at your call-site when strict validation is required.

        Args:
            level: Logging level — string name or integer constant.
        Returns:
            ``self``, for method chaining.
        Example::
            lab().with_level("WARNING").build(__name__)
            lab().with_level(logging.DEBUG).build(__name__)
        """

        self._level = normalise_level_name(level)

        return self

    def build(self, name: str) -> Logger:
        """
        Materialise the configured `logging.Logger`.

        Construction order:
        1. Raise `BuilderError` if neither a profile nor any experiments are queued.
        2. Retrieve (or create) the named logger and clear its handlers.
        3. Apply the profile (if any) — lab profile builds an
           intermediate logger; its handlers are migrated and the
           intermediate is cleaned up.
        4. Apply each queued experiment in order, attaching the returned handlers.
        5. Set the final level and disable propagation.

        Args:
            name: Logger name passed to `logging.getLogger`,
            typically ``__name__``.
        Returns:
            A fully configured `logging.Logger` with
            ``propagate = False``.
        Raises:
            `BuilderError`:
                If no experiments or profile have been queued.
            `ExperimentNotFoundError`:
                If a queued experiment is not in the registry.
            `ProfileNotFoundError`:
                If the queued profile is not in the registry.
        Example::
            logger = lab().with_experiment("AI").with_level("INFO").build(__name__)
        """

        if self._profile is None and not self._experiments:
            raise BuilderError(name)

        # Initialize logger and clear the handlers
        logger = getLogger(name)
        clear_handlers(logger)

        # Apply profile first — steal its handlers onto our logger.
        if self._profile is not None:
            profile_factory = get_profile(self._profile)
            profile_logger = profile_factory(name + ".__profile__", self._level)

            for handler in profile_logger.handlers:
                logger.addHandler(handler)

            clear_handlers(profile_logger)  # prevent intermediate logger double-emitting

        # Layer individual experiments on top of the profile (if any).
        for exp_type in self._experiments:

            # TEST A THEORY
            if type(exp_type) is TheoryType:
                experiment = get_theory(exp_type)

            else:
                experiment = get_experiment(exp_type)

            for handler in experiment(self._level):
                logger.addHandler(handler)

        logger.setLevel(self._level)
        logger.propagate = False

        return logger


def lab() -> LabBuilder:
    """
    Return a fresh `LabBuilder()` instance.

    This is the intended entry point for fluent logger construction::

        from logger_lab import lab

        logger = (
            lab()
            .with_experiment("standard")
            .with_level("DEBUG")
            .build(__name__)
        )

    Returns:
        A new, unconfigured :class:`LabBuilder`.
    """

    return LabBuilder()
