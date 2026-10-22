"""RELAY: subscribers get every record they ask for, without breaking logging when they fail."""

import logging

from logger_lab import ExperimentType, lab
from logger_lab.experiments.relay import RelayHandler


def test_subscriber_gets_each_record():
    """A subscriber is called with the `LogRecord` itself, on the logging thread when there's no ASYNC."""

    seen: list[logging.LogRecord] = []
    logger = lab().with_subscriber(seen.append).with_level("DEBUG").build("app.relay")

    logger.debug("one")
    logger.warning("two")

    assert [r.getMessage() for r in seen] == ["one", "two"]
    assert seen[0].name == "app.relay"


def test_with_subscriber_brings_relay_with_it():
    """No need to queue RELAY by hand; queuing it as well isn't a duplicate."""

    assert lab().with_subscriber(print).plan() == [ExperimentType.RELAY]
    assert lab().with_experiment("standard").with_subscriber(print).plan() == [ExperimentType.STANDARD, ExperimentType.RELAY]
    assert lab().with_experiment("RELAY").with_subscriber(print).plan() == [ExperimentType.RELAY]


def test_each_subscriber_has_its_own_level():
    """level=None lets the logger decide; a level filters just that subscriber."""

    everything: list[str] = []
    errors_only: list[str] = []
    logger = (
        lab().with_level("DEBUG")
        .with_subscriber(lambda r: everything.append(r.getMessage()))
        .with_subscriber(lambda r: errors_only.append(r.getMessage()), level="ERROR")
        .build("app.relay")
    )

    logger.info("fine")
    logger.error("broken")

    assert everything == ["fine", "broken"]
    assert errors_only == ["broken"]
    assert [h.level for h in logger.handlers] == [logging.NOTSET, logging.ERROR]


def test_relay_without_subscribers_adds_nothing():
    """RELAY with nobody listening builds no handler."""

    assert lab().with_experiment("RELAY").with_experiment("minimalist").build("app.quiet").handlers[0].__class__ is not RelayHandler
    assert len(lab().with_experiment("RELAY").with_experiment("minimalist").build("app.quiet").handlers) == 1


def test_a_failing_subscriber_does_not_break_logging(capsys):
    """A subscriber that raises is reported like any handler error; other outputs still get the record."""

    good: list[str] = []

    def bad(record: logging.LogRecord) -> None:
        """Always fails."""

        raise RuntimeError("subscriber bug")

    logger = lab().with_subscriber(bad).with_subscriber(lambda r: good.append(r.getMessage())).build("app.relay")

    logger.warning("still delivered")

    assert good == ["still delivered"]
    assert "subscriber bug" in capsys.readouterr().err
