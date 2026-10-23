"""
``LabBuilder``, the one composer, and ``lab()``, its entry point.

A logger is composed by four kinds of building block, each with its own method:

* ``with_output(name, **options)``: where feedback goes (console, file, relay);
* ``with_feature(name, on=, **options)``: extra behavior on an output (detail, rotation);
* ``with_format(name, on=)``: how a record looks (rich, text, JSON);
* ``with_catalyst(name, **options)``: how every record flows (async).

``with_profile()`` starts from a common composition. ``with_theory()`` adds a building block
still in trial. The ``with_*`` methods only record what was asked for. `plan()` checks it
against the specs and returns a `Composition`, and `build()` builds exactly that.
"""

import inspect
import warnings
from dataclasses import dataclass, field
from enum import Enum
from functools import partial
from logging import INFO, Handler, Logger, getLogger
from typing import Any, TypeVar, cast

from logger_lab.core.enums import Catalyst, Feature, Format, Kind, Output, ProfileType, TheoryType, value_of
from logger_lab.core.registry import PROFILES, get_profile, get_theory, spec_for
from logger_lab.core.specs import CatalystSpec, FeatureSpec, FormatSpec, OutputPlan, OutputSpec, Subscriber
from logger_lab.logging_kernel.errors import (
    BuilderError, CompositionError, LabError, ProfileSuggestionWarning, RegistrationError,
)
from logger_lab.logging_kernel.handlers import install_handlers
from logger_lab.logging_kernel.normalizers import normalize_level_name, normalize_name

OutputName = Output | TheoryType  # An output, or a theory registered as one
FeatureName = Feature | TheoryType
FormatName = Format | TheoryType
CatalystName = Catalyst | TheoryType
SpecT = TypeVar("SpecT", OutputSpec, FeatureSpec, FormatSpec, CatalystSpec)  # The spec type spec_of() returns


@dataclass
class PlannedOutput:
    """One output in a `Composition`: its options, features and format, all checked."""

    output: OutputName
    spec: OutputSpec
    options: dict[str, object]
    features: dict[FeatureName, dict[str, object]] = field(default_factory=dict)
    format: FormatName | None = None
    format_options: dict[str, object] = field(default_factory=dict)
    origin: str = "queued"


@dataclass
class Composition:
    """What `LabBuilder.plan()` returns: the outputs (in order) and the catalysts to build."""

    outputs: list[PlannedOutput]
    catalysts: list[tuple[CatalystName, CatalystSpec, dict[str, object]]]

    def names(self) -> dict[str, Any]:
        """A compact summary for tests and debugging: ``{"CONSOLE": {...}, "FILE": {...}, "catalysts": [...]}``."""

        summary: dict[str, Any] = {
            value_of(planned.output): {
                "format": value_of(planned.format) if planned.format is not None else None,
                "features": sorted(value_of(feature) for feature in planned.features),
            }
            for planned in self.outputs
        }
        summary["catalysts"] = [value_of(name) for name, _, _ in self.catalysts]

        return summary


class LabBuilder:
    """
    Fluent builder for composing a logger from outputs, features, formats and catalysts.

    Each ``with_*`` method records its input and returns ``self``; nothing is built until
    `build()`. Asking for the same building block again **configures** it: options merge,
    later values win. A logger holds at most one output of each kind.

    Composition rules, enforced by `plan()` (`CompositionError` names the fix):
    * a feature or format attaches to every queued output it fits, or to ``on=``'s output;
      it never brings an output with it;
    * one detail feature and one format per output, and only where they work;
    * options must be ones the building block declares;
    * one profile per builder, and one catalyst per group (e.g. one dispatcher).

    Hand-queued outputs that a profile already composes warn with `ProfileSuggestionWarning`.
    """

    def __init__(self) -> None:
        """Start empty: no profile, nothing queued, level unset (INFO at build)."""

        # Underscored: the builder's recorded state, read only through plan()/build().
        self._outputs: dict[OutputName, dict[str, object]] = {}
        self._origins: dict[OutputName, str] = {}
        self._features: dict[tuple[FeatureName, Output | None], dict[str, object]] = {}
        self._formats: dict[tuple[FormatName, Output | None], dict[str, object]] = {}
        self._catalysts: dict[CatalystName, dict[str, object]] = {}
        self._profile: ProfileType | None = None
        self._origin = "queued"  # Becomes "from profile '…'" while a profile's recipe runs
        self._level: int | None = None
        self._subscribers: list[tuple[Subscriber, int | None]] = []

    ###################################
    # The four kinds, one method each #
    ###################################

    def with_output(self, output: Output | str, **options: object) -> "LabBuilder":
        """
        Add an output, or configure it if this logger already has it (from a profile, say).

        Args:
            output:    ``"console"``, ``"file"`` or ``"relay"`` (member or value string).
            **options: The output's options, e.g. ``log_dir=``/``filename=`` for file,
                       ``stream=`` for console. Repeated calls merge.
        Returns:
            ``self``, for method chaining.
        Raises:
            `InvalidNameError`: If *output* isn't an output.
        Example::
            lab().with_profile("investigator").with_output("file", log_dir=user_dir)
        """

        self.add_output(normalize_name(Output, output, "output"), options)

        return self

    def with_feature(self, feature: Feature | str, on: Output | str | None = None, **options: object) -> "LabBuilder":
        """
        Add a feature to every queued output it fits, or only to *on*.

        Args:
            feature:   ``"MINIMAL"``, ``"VERBOSE"``, ``"ROTATING"`` or ``"TIMED"`` (member or value string).
            on:        The output to attach to; needed only when it fits several queued outputs.
            **options: The feature's options, e.g. ``max_bytes=`` for ROTATING, or ``every=``,
                       ``unit=``, ``day=``, ``at=`` and ``utc=`` for TIMED. Repeated calls merge.
        Returns:
            ``self``, for method chaining.
        Raises:
            `InvalidNameError`: If *feature* or *on* isn't a valid name.
        Example::
            lab().with_profile("investigator").with_feature("TIMED", at="02:00")
            lab().with_profile("investigator").with_feature("MINIMAL", on="console")
        """

        self.merge(self._features, (normalize_name(Feature, feature, "feature"), resolve_on(on)), options)

        return self

    def with_format(self, format_: Format | str, on: Output | str | None = None, **options: object) -> "LabBuilder":
        """
        Set the format of every queued output it fits, or only of *on*.

        Args:
            format_:   ``"RICH"``, ``"TEXT"`` or ``"JSON"`` (member or value string).
            on:        The output to set it on; needed only when it fits several queued outputs.
            **options: The format's options (none today).
        Returns:
            ``self``, for method chaining.
        Raises:
            `InvalidNameError`: If *format_* or *on* isn't a valid name.
        Example::
            lab().with_profile("investigator").with_format("JSON", on="file")   # a JSON-lines file
        """

        self.merge(self._formats, (normalize_name(Format, format_, "format"), resolve_on(on)), options)

        return self

    def with_catalyst(self, catalyst: Catalyst | str, **options: object) -> "LabBuilder":
        """
        Add a catalyst: a change to how every record flows to the outputs.

        Args:
            catalyst:  ``"ASYNC"`` (member or value string).
            **options: The catalyst's options (none today).
        Returns:
            ``self``, for method chaining.
        Raises:
            `InvalidNameError`: If *catalyst* isn't a catalyst.
        Example::
            lab().with_profile("investigator").with_catalyst("ASYNC")
        """

        self.merge(self._catalysts, normalize_name(Catalyst, catalyst, "catalyst"), options)

        return self

    ###################################
    # Profiles, theories, subscribers #
    ###################################

    def with_profile(self, profile: ProfileType | str) -> "LabBuilder":
        """
        Start from a profile, which is a common composition. Then add or configure on top.

        Args:
            profile: ``"investigator"``, ``"observer"``, ``"conspiracy_theorist"``, ``"ai_agent"`` or ``"gui"``.
        Returns:
            ``self``, for method chaining.
        Raises:
            `InvalidNameError`: If *profile* isn't a profile.
            `CompositionError`: If a profile was already chosen (one per builder).
        Example::
            lab().with_profile("investigator").with_feature("ROTATING").build(__name__)
        """

        member = normalize_name(ProfileType, profile, "profile")

        if self._profile is not None:
            raise CompositionError(
                f"this builder already uses the '{value_of(self._profile)}' profile, and a logger takes one. "
                f"Add outputs, features or formats to it instead of a second profile"
            )

        self._profile = member
        self._origin = f"from profile '{value_of(member)}'"

        try:
            get_profile(member).recipe(self)

        finally:
            self._origin = "queued"

        return self

    def with_theory(self, theory: TheoryType | str, on: Output | str | None = None, **options: object) -> "LabBuilder":
        """
        Add a building block still in trial; it acts as the kind it was registered as.

        Args:
            theory:    A `TheoryType` member or value string.
            on:        For a feature or format theory: the output to attach to.
            **options: The theory's options.
        Returns:
            ``self``, for method chaining.
        Raises:
            `InvalidNameError`: If *theory* isn't a theory.
            `TheoryNotFoundError`: If *theory* is still a placeholder.
            `CompositionError`: If *on* is given for an output or catalyst theory, which can't use it.
        Example::
            lab().with_profile("gui").with_theory("THROTTLE", per_second=20)   # once THROTTLE is in trial
        """

        member = normalize_name(TheoryType, theory, "theory")
        kind, _ = get_theory(member)

        if on is not None and kind in (Kind.OUTPUT, Kind.CATALYST):
            kind_name = "an output" if kind is Kind.OUTPUT else "a catalyst"
            raise CompositionError(f"'{value_of(member)}' is {kind_name} theory, so on= doesn't apply to it. "
                                   f"on= is for feature and format theories")

        if kind is Kind.OUTPUT:
            self.add_output(member, options)
        elif kind is Kind.FEATURE:
            self.merge(self._features, (member, resolve_on(on)), options)
        elif kind is Kind.FORMAT:
            self.merge(self._formats, (member, resolve_on(on)), options)
        else:
            self.merge(self._catalysts, member, options)

        return self

    def with_subscriber(self, callback: Subscriber, level: int | str | None = None) -> "LabBuilder":
        """
        Hand every record to *callback* as it is logged. This brings the ``relay`` output with it.

        Each call adds a subscriber with its own optional *level*. With ``None``, the
        logger's level decides. The callback gets the `logging.LogRecord`, so treat it as
        read-only. With ``ASYNC`` it runs on the dispatch worker, otherwise on the thread
        that logged. For Qt, pass a signal's ``emit``.

        Args:
            callback: Called with each record that passes *level*.
            level:    Minimum level for this subscriber: a name, an integer, or ``None``.
        Returns:
            ``self``, for method chaining.
        Example::
            lab().with_profile("gui").with_subscriber(relay.record_logged.emit).build("LabFrame.feedback")
        """

        self._subscribers.append((callback, None if level is None else normalize_level_name(level)))

        if Output.RELAY not in self._outputs:
            self._outputs[Output.RELAY] = {}
            self._origins[Output.RELAY] = "added by with_subscriber()"

        return self

    def with_level(self, level: int | str) -> "LabBuilder":
        """
        Set the logging level of the logger. If never called, the level is ``INFO``.

        Args:
            level: A level name (case-insensitive, custom ones too) or an integer ``0`` or above.
        Returns:
            ``self``, for method chaining.
        Raises:
            `InvalidLevelError`: For an unknown name or an invalid number.
        Example::
            lab().with_profile("investigator").with_level("DEBUG").build(__name__)
        """

        self._level = normalize_level_name(level)

        return self

    ############
    # Planning #
    ############

    def plan(self) -> Composition:
        """
        Check the composition and return it, without building anything.

        Resolves every feature and format to its output(s), merges options over each
        building block's defaults, runs each spec's checks, and applies the composition rules.

        Returns:
            The checked `Composition`.
        Raises:
            `BuilderError`: If nothing is queued.
            `CompositionError`: If the composition can't work (the message says how to fix it).
        Warns:
            `ProfileSuggestionWarning`: If hand-queued outputs exactly match a profile.
        Example::
            lab().with_profile("investigator").with_format("JSON", on="file").plan().names()
            # → {"CONSOLE": {"format": "RICH", ...}, "FILE": {"format": "JSON", ...}, "catalysts": []}
        """

        if not self._outputs:
            if self._catalysts:
                first = value_of(next(iter(self._catalysts)))
                raise CompositionError(f"'{first}' needs an output to work on: add .with_output(), "
                                       f"or start from a profile such as 'investigator'")

            raise BuilderError("nothing is queued: add a profile (.with_profile()) or an output (.with_output())")

        planned: dict[OutputName, PlannedOutput] = {}

        for output, options in self._outputs.items():
            output_spec = spec_of(output, OutputSpec)
            planned[output] = PlannedOutput(output, output_spec, merged_options(output_spec, options, output),
                                            origin=self._origins[output])

        for (feature, on), options in self._features.items():
            feature_spec = spec_of(feature, FeatureSpec)
            resolved = merged_options(feature_spec, options, feature)
            resolved = feature_spec.check(resolved) if feature_spec.check else resolved
            group = feature_spec.group

            for target in attach_targets(feature, feature_spec.fits, on, planned):
                rivals = [other for other in target.features if group and group_of(other) == group]

                if rivals and rivals[0] != feature:
                    raise CompositionError(
                        f"'{value_of(rivals[0])}' and '{value_of(feature)}' both set the {group} of the "
                        f"{value_of(target.output).lower()} output; keep one"
                    )

                target.features[feature] = {**target.features.get(feature, {}), **resolved}

        for (format_, on), options in self._formats.items():
            format_spec = spec_of(format_, FormatSpec)
            resolved = merged_options(format_spec, options, format_)

            for target in attach_targets(format_, format_spec.fits, on, planned):
                current = target.format

                if current is not None:
                    if current != format_:
                        raise CompositionError(
                            f"the {value_of(target.output).lower()} output already has format '{value_of(current)}'; "
                            f"one format per output. Drop one, or use on= to set each output's format"
                        )

                target.format, target.format_options = format_, resolved

        for target in planned.values():
            finish_output(target)

        catalysts = self.plan_catalysts()

        composition = Composition(list(planned.values()), catalysts)

        if self._profile is None:
            suggest_profile(self, composition)

        return composition

    def build(self, name: str) -> Logger:
        """
        Build the planned logger: every output's handlers, wrapped by the catalysts, swapped on atomically.

        1. `plan()` raises before anything is touched, so a bad composition never wipes an
           existing logger.
        2. Build each output's handlers from its `OutputPlan`. The catalysts (e.g. ``ASYNC``)
           wrap them. `install_handlers` swaps the result onto the logger in one step, and
           releases the old handlers. A thread logging meanwhile sees the old handlers or the
           new ones, never a mix.
        3. Set the level (``INFO`` unless `with_level()` was called) and disable propagation.

        Thread-safe: any number of threads may build loggers at once, including the same
        name. A single `LabBuilder` is not meant to be shared between threads while it is
        being configured.

        Args:
            name: Logger name passed to `logging.getLogger`, typically ``__name__``.
        Returns:
            A fully configured `logging.Logger` with ``propagate = False``.
        Raises:
            `BuilderError` / `CompositionError`: As `plan()`.
            `LogFileClashError`: If another logger has this logger's file open with a different setup.
        Example::
            logger = lab().with_profile("investigator").build(__name__)
        """

        composition = self.plan()
        level = self._level if self._level is not None else INFO
        logger = getLogger(name)
        subscribers = tuple(self._subscribers)

        outputs = [
            partial(target.spec.build, OutputPlan(
                output=target.output,
                options=target.options,
                features=target.features,
                format=target.format,
                format_options=target.format_options,
                logger_name=name,
                subscribers=subscribers,
            ))
            for target in composition.outputs
        ]

        def dispatch(*, handlers: list[Handler]) -> list[Handler]:
            """Let each catalyst wrap the outputs, in the order they were added."""

            for _, spec, options in composition.catalysts:
                handlers = spec.build(handlers, logger_name=name, options=options)

            return handlers

        install_handlers(logger, outputs, dispatcher=dispatch if composition.catalysts else None)
        logger.setLevel(level)
        logger.propagate = False

        return logger

    ##########################
    # Recording and planning #
    ##########################

    def add_output(self, output: OutputName, options: dict[str, object]) -> None:
        """Add *output* or merge *options* into it, recording where it first came from."""

        self.merge(self._outputs, output, options)
        self._origins.setdefault(output, self._origin)

    def replayed_on(self, profile: ProfileType) -> "LabBuilder":
        """A new builder that starts from *profile*, then queues everything this one queued."""

        replay = LabBuilder().with_profile(profile)

        for output, options in self._outputs.items():
            replay.add_output(output, options)

        for table, own in ((replay._features, self._features), (replay._formats, self._formats),
                           (replay._catalysts, self._catalysts)):
            for key, options in own.items():
                self.merge(table, key, options)

        replay._subscribers = list(self._subscribers)

        return replay

    def blocks(self) -> "Blocks":
        """What is queued, by name only. Used to compare a composition with a profile's."""

        return Blocks(
            frozenset(self._outputs),
            frozenset(feature for feature, _ in self._features),
            frozenset(format_ for format_, _ in self._formats),
            frozenset(self._catalysts),
        )

    @staticmethod
    def merge(table: dict[Any, dict[str, object]], key: Any, options: dict[str, object]) -> None:
        """Merge *options* into ``table[key]``. Later values win."""

        table[key] = {**table.get(key, {}), **options}

    def plan_catalysts(self) -> list[tuple[CatalystName, CatalystSpec, dict[str, object]]]:
        """Resolve the catalysts' options and enforce one catalyst per group."""

        catalysts = []
        groups: dict[str, CatalystName] = {}

        for member, options in self._catalysts.items():
            spec = spec_of(member, CatalystSpec)

            if spec.group is not None:
                if spec.group in groups:
                    raise CompositionError(f"'{value_of(groups[spec.group])}' and '{value_of(member)}' are both "
                                           f"{spec.group} catalysts; a logger takes one")

                groups[spec.group] = member

            catalysts.append((member, spec, merged_options(spec, options, member)))

        return catalysts


#######################################
# Planning helpers (no builder state) #
#######################################

def resolve_on(on: Output | str | None) -> Output | None:
    """Resolve an ``on=`` argument to an `Output`."""

    return None if on is None else normalize_name(Output, on, "output")


def spec_of(member: OutputName | FeatureName | FormatName | CatalystName, spec_type: type[SpecT]) -> SpecT:
    """
    The spec of a built-in member or a registered theory, checked to be *spec_type*.

    Raises:
        `RegistrationError`: If the member's spec is of another kind.
    """

    spec = get_theory(member)[1] if isinstance(member, TheoryType) else spec_for(member)

    if not isinstance(spec, spec_type):
        raise RegistrationError(member, f"it is not a {spec_type.__name__}")

    return cast(SpecT, spec)  # Checked just above; type checkers don't narrow through a TypeVar


def group_of(member: FeatureName) -> str | None:
    """A feature's exclusive group, if any."""

    return spec_of(member, FeatureSpec).group


def merged_options(spec: OutputSpec | FeatureSpec | FormatSpec | CatalystSpec, given: dict[str, object],
                   member: Enum) -> dict[str, object]:
    """Merge *given* over *spec*'s defaults, rejecting options it doesn't declare."""

    unknown = sorted(set(given) - set(spec.options))

    if unknown:
        valid = ", ".join(spec.options) or "none"
        raise CompositionError(
            f"'{value_of(member)}' has no option {', '.join(map(repr, unknown))}; its options: {valid}"
        )

    return {**spec.options, **given}


def attach_targets(member: FeatureName | FormatName, fits: frozenset[Output], on: Output | None,
                   planned: dict[OutputName, PlannedOutput]) -> list[PlannedOutput]:
    """The queued outputs a feature or format attaches to. Raises a `CompositionError` naming the fix if none fits."""

    label = value_of(member)
    fits_text = " or ".join(sorted(value_of(output).lower() for output in fits))

    if on is not None:
        if on not in fits:
            raise CompositionError(f"'{label}' works on {fits_text} outputs, not {value_of(on).lower()}")

        if on not in planned:
            name = value_of(on).lower()
            raise CompositionError(f"'{label}' has on='{name}', but no {name} output "
                                   f"is queued: add .with_output('{name}') or use a profile")

        return [planned[on]]

    targets = [target for output, target in planned.items() if output in fits]

    if not targets:
        first = sorted(value_of(output).lower() for output in fits)[0]
        raise CompositionError(
            f"'{label}' needs a {fits_text} output: add .with_output('{first}'), "
            f"or start from a profile such as '{profile_with(first)}'"
        )

    return targets


def finish_output(target: PlannedOutput) -> None:
    """
    Default the format, check the output can render it, check the features against it,
    and run the output's own check.
    """

    output_name = value_of(target.output).lower()

    if target.format is None and target.spec.default_format is not None:
        target.format = target.spec.default_format

    format_ = target.format

    if format_ is not None and format_ not in target.spec.formats:  # CR-17: FormatSpec.fits isn't enough
        known = ", ".join(sorted(value_of(f) for f in target.spec.formats)) or "none"
        raise CompositionError(f"the {output_name} output can't render the '{value_of(format_)}' format; "
                               f"the formats it renders: {known}")

    for feature in target.features:
        formats = spec_of(feature, FeatureSpec).formats

        if formats is not None and format_ not in formats:
            format_name = value_of(format_) if format_ is not None else "unformatted"
            raise CompositionError(
                f"'{value_of(feature)}' has no effect on the {format_name} format of the "
                f"{output_name} output (JSON always carries every field)"
            )

    if target.spec.check is not None:
        target.spec.check(OutputPlan(target.output, target.options, target.features, target.format,
                                     target.format_options, "<plan>"))


@dataclass(frozen=True)
class Blocks:
    """The names of what a builder has queued, by kind. Options and ``on=`` are left out."""

    outputs: frozenset[OutputName]
    features: frozenset[FeatureName]
    formats: frozenset[FormatName]
    catalysts: frozenset[CatalystName]

    @property
    def size(self) -> int:
        """How many building blocks, of every kind."""

        return len(self.outputs) + len(self.features) + len(self.formats) + len(self.catalysts)

    def contains(self, other: "Blocks") -> bool:
        """True when *other* has the same outputs and nothing else that this doesn't have."""

        return (self.outputs == other.outputs and other.features <= self.features
                and other.formats <= self.formats and other.catalysts <= self.catalysts)


def suggest_profile(builder: LabBuilder, composition: Composition) -> None:
    """
    Warn when two or more outputs were queued by hand and a profile already provides them.

    A profile is only suggested when following the advice works. The hand-made composition
    is replayed on top of the profile, and the result must plan to exactly the same
    composition. So the suggestion never adds anything, and never leads to a clash. A
    profile whose blocks aren't all queued is skipped without replaying. The most specific
    match wins.

    Note: it runs each profile's recipe again on every such plan (CR-22). That costs a few
    microseconds at setup time, so nothing is cached.
    """

    queued = builder.blocks()

    if len(queued.outputs) < 2:
        return

    candidates = [member for member, blocks in profile_blocks() if queued.contains(blocks)]

    for profile in reversed(candidates):  # Most specific first
        try:
            replayed = builder.replayed_on(profile).plan()

        except LabError:  # The profile clashes with something queued by hand
            continue

        if replayed.names() == composition.names():
            warning = ProfileSuggestionWarning(value_of(profile), get_profile(profile).summary)
            warnings.warn(warning, stacklevel=caller_stacklevel())
            return


def caller_stacklevel() -> int:
    """
    The ``stacklevel`` that points a warning at the first frame outside logger-lab (CR-16).

    A fixed number was right through ``build()`` but one frame off through ``plan()``.
    Walking the stack is right for every entry point.
    """

    level = 1
    frame = inspect.currentframe()
    frame = frame.f_back if frame is not None else None  # The function that will warn: stacklevel 1

    while frame is not None and frame.f_globals.get("__name__", "").startswith("logger_lab"):
        frame = frame.f_back
        level += 1

    return level


def profile_blocks() -> list[tuple[ProfileType, Blocks]]:
    """Every profile's building blocks, simplest profile first (fewest building blocks, then by name)."""

    found = []

    for member, spec in PROFILES.items():
        probe = LabBuilder()
        spec.recipe(probe)
        found.append((member, probe.blocks()))

    return sorted(found, key=lambda item: (item[1].size, value_of(item[0])))


def profile_with(output: str) -> str:
    """The simplest profile that includes *output* (by value, lower-case), for error messages."""

    for member, blocks in profile_blocks():
        if any(value_of(o).lower() == output for o in blocks.outputs):
            return value_of(member).lower()

    return "investigator"


def lab() -> LabBuilder:
    """
    Return a fresh `LabBuilder()`. This is the one way to build a logger.

    Returns:
        A new, unconfigured `LabBuilder`.
    Example::
        logger = lab().with_profile("investigator").build(__name__)
    """

    return LabBuilder()

