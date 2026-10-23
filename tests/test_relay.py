"""RELAY: subscribers get every record they ask for, without breaking logging when they fail or log themselves."""

import logging
from pathlib import Path

from logger_lab import drain, lab
from logger_lab.outputs.relay import RelayHandler


def test_with_subscriber_brings_one_relay_and_hands_over_the_record():
    """No need to add the relay by hand, and adding it too is still one relay. Subscribers get the LogRecord itself."""

    relay = {"RELAY": {"format": None, "features": []}, "catalysts": []}

    assert lab().with_subscriber(print).plan().names() == relay
    assert lab().with_output("relay").with_subscriber(print).plan().names() == relay

    seen: list[logging.LogRecord] = []
    logger = lab().with_subscriber(seen.append).with_level("DEBUG").build("app.relay")
    logger.debug("one")
    logger.warning("two")

    assert [r.getMessage() for r in seen] == ["one", "two"] and seen[0].name == "app.relay"


def test_each_subscriber_has_its_own_level():
    """level=None lets the logger decide. A level filters just that subscriber."""

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

    assert everything == ["fine", "broken"] and errors_only == ["broken"]
    assert [h.level for h in logger.handlers] == [logging.NOTSET, logging.ERROR]


def test_a_relay_without_subscribers_adds_nothing():
    """The relay output with nobody listening builds no handler."""

    handlers = lab().with_output("relay").with_output("console").build("app.quiet").handlers

    assert len(handlers) == 1 and not isinstance(handlers[0], RelayHandler)


def test_a_failing_subscriber_does_not_break_logging(capsys):
    """A subscriber that raises is reported like any handler error. The other subscribers still get the record."""

    good: list[str] = []

    def bad(_record: logging.LogRecord) -> None:
        """Always fails."""

        raise RuntimeError("subscriber bug")

    logger = lab().with_subscriber(bad).with_subscriber(lambda r: good.append(r.getMessage())).build("app.relay")
    logger.warning("still delivered")

    assert good == ["still delivered"]
    assert "subscriber bug" in capsys.readouterr().err


def subscriber_that_logs(logger_name: str, calls: list[str]):
    """A subscriber that logs to the logger it subscribes to (EX-7), capped so a regression can't hang the run."""

    def subscriber(record: logging.LogRecord) -> None:
        """Record the call, then log from inside the subscriber."""

        calls.append(record.getMessage())

        if len(calls) < 50:
            logging.getLogger(logger_name).warning("logged inside the subscriber")

    return subscriber


def test_a_subscriber_that_logs_does_not_feed_itself():
    """EX-7: the record logged inside the subscriber reaches the file, but no subscriber again."""

    calls: list[str] = []
    logger = lab().with_output("file").with_subscriber(subscriber_that_logs("app.echo", calls)).build("app.echo")

    logger.info("from the app")
    text = Path("logs/app.log").read_text(encoding="utf-8")

    assert calls == ["from the app"]
    assert "from the app" in text and "logged inside the subscriber" in text


def test_the_echo_guard_holds_behind_async():
    """EX-7 with ASYNC: the echo is queued and delivered later, and is still never relayed."""

    calls: list[str] = []
    logger = (
        lab().with_output("file").with_catalyst("ASYNC")
        .with_subscriber(subscriber_that_logs("app.echo_async", calls)).build("app.echo_async")
    )

    logger.info("from the app")

    assert drain(5)
    assert calls == ["from the app"]
    assert "logged inside the subscriber" in Path("logs/app.log").read_text(encoding="utf-8")
