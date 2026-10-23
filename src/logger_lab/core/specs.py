"""
Specs: how each building block describes itself to the registry and the builder.

Every output, feature, format, catalyst and profile is registered with a small frozen spec:
what it fits, which options it takes (with their defaults), and what it builds. The builder
checks a composition against these specs, so every composition rule lives in one place.
"""

from dataclasses import dataclass, field
from logging import Handler
from collections.abc import Callable, Mapping
from typing import TYPE_CHECKING, Any

from logger_lab.core.enums import Catalyst, Feature, Format, Output, ProfileType, TheoryType

if TYPE_CHECKING:  # type-only: the builder imports the registry, which imports this module
    from logger_lab.core.builder import LabBuilder

Subscriber = Callable[[Any], object]  # Called with each logging.LogRecord it lets through


@dataclass
class OutputPlan:
    """Everything one output needs to build its handlers: its options, features and format."""

    output: Output | TheoryType
    options: dict[str, object]
    features: dict[Feature | TheoryType, dict[str, object]]
    format: Format | TheoryType | None  # None for an output without formats (relay)
    format_options: dict[str, object]
    logger_name: str
    subscribers: tuple[tuple[Subscriber, int | None], ...] = ()

    @property
    def detail(self) -> str:
        """``"minimal"``, ``"verbose"`` or ``"standard"``, from the detail features."""

        if Feature.MINIMAL in self.features:
            return "minimal"

        if Feature.VERBOSE in self.features:
            return "verbose"

        return "standard"


@dataclass(frozen=True)
class OutputSpec:
    """An output: where feedback goes. *build* turns an `OutputPlan` into handlers."""

    member: Output | TheoryType
    build: Callable[[OutputPlan], list[Handler]]
    options: Mapping[str, object] = field(default_factory=dict)
    formats: frozenset[Format] = frozenset()  # Formats it accepts; empty for outputs without one
    default_format: Format | None = None      # Used when no format is set
    check: Callable[[OutputPlan], None] | None = None  # Raises CompositionError for a plan it can't build


@dataclass(frozen=True)
class FeatureSpec:
    """A feature: extra behavior on an output. Interpreted by the output it is attached to."""

    member: Feature | TheoryType
    fits: frozenset[Output]
    options: Mapping[str, object] = field(default_factory=dict)
    group: str | None = None                  # Features in one group exclude each other on an output
    formats: frozenset[Format] | None = None  # Formats it works with; None means any
    check: Callable[[dict[str, object]], dict[str, object]] | None = None  # Validates/normalizes options


@dataclass(frozen=True)
class FormatSpec:
    """A format: how a record looks on the outputs it fits."""

    member: Format | TheoryType
    fits: frozenset[Output]
    options: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class CatalystSpec:
    """A catalyst: how every record flows. *build* wraps the built output handlers."""

    member: Catalyst | TheoryType
    build: Callable[..., list[Handler]]  # build(handlers, *, logger_name, options) -> the logger's handlers
    options: Mapping[str, object] = field(default_factory=dict)
    group: str | None = None  # Catalysts in one group exclude each other (e.g. "dispatch": ASYNC, PROCESS)


@dataclass(frozen=True)
class ProfileSpec:
    """A profile: a common composition, written as builder calls (*recipe*) so it obeys every rule."""

    member: ProfileType
    recipe: Callable[["LabBuilder"], "LabBuilder"]
    summary: str
