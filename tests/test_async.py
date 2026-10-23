"""ASYNC: records are queued on the caller's thread and written on the one dispatch worker, without ever hanging."""

import logging
import re
import subprocess
import sys
import textwrap
import threading
import time
from pathlib import Path

import pytest

from logger_lab import BuilderError, drain, lab
from logger_lab.logging_kernel import SHARED_FILES, AsyncHandler, clear_handlers, dispatch, stop_worker

from helpers import run_together


def async_handler(logger: logging.Logger) -> AsyncHandler:
    """Return *logger*'s one handler, checked to be the `AsyncHandler`."""

    (handler,) = logger.handlers
    assert isinstance(handler, AsyncHandler)

    return handler


def log_text() -> str:
    """Return ``logs/app.log`` after every queued record is written."""

    assert drain(5)

    return Path("logs/app.log").read_text(encoding="utf-8")


def test_one_handler_queues_and_the_worker_writes():
    """The logger holds a single `AsyncHandler` around its outputs. The dispatch worker does the writing."""

    writers: list[str] = []
    logger = (
        lab().with_output("file").with_catalyst("ASYNC")
        .with_subscriber(lambda record: writers.append(threading.current_thread().name)).build("app.async")
    )

    logger.info("queued")

    assert [type(t).__name__ for t in async_handler(logger).targets] == ["LabFileHandler", "RelayHandler"]
    assert "queued" in log_text()
    assert writers == [dispatch.WORKER_NAME]


def test_a_record_is_final_when_logged():
    """Unlike the stdlib QueueHandler, the traceback is kept. A mutable argument changed afterwards changes nothing."""

    logger = lab().with_output("file").with_catalyst("ASYNC").build("app.async")
    payload = ["before"]

    logger.info("payload=%s", payload)
    payload[0] = "after"

    try:
        raise ValueError("kaboom")
    except ValueError:
        logger.exception("it broke")

    text = log_text()

    assert "payload=['before']" in text
    assert "Traceback (most recent call last)" in text and "ValueError: kaboom" in text


def test_order_is_kept():
    """One FIFO queue: records come out in the order they went in."""

    logger = lab().with_output("file").with_catalyst("ASYNC").build("app.async")

    for n in range(500):
        logger.info("n=%d", n)

    assert [int(m) for m in re.findall(r"n=(\d+)", log_text())] == list(range(500))


def test_one_worker_for_the_whole_process():
    """
    Eight threads logging through eight async loggers at the same moment still share one worker thread.

    (Eight threads through one async rotating file: test_threads.)
    """

    loggers = [lab().with_output("file").with_catalyst("ASYNC").build(f"app.w{i}") for i in range(8)]

    def burst(i: int) -> None:
        """Log a burst through logger *i*."""

        for n in range(50):
            loggers[i].info("burst %d", n)

    run_together(len(loggers), burst)

    assert drain(5)
    assert [t.name for t in threading.enumerate()].count(dispatch.WORKER_NAME) == 1


def test_async_with_nothing_built_fails_the_build():
    """
    A relay with no subscribers builds no handler, so ASYNC has nothing to wrap.

    (No output at all: test_composition.)
    """

    with pytest.raises(BuilderError, match="nothing for it to dispatch to"):
        lab().with_output("relay").with_catalyst("ASYNC").build("app.empty_relay")


def test_a_failing_output_does_not_cost_the_others_the_record(capsys, monkeypatch):
    """KN-34: AsyncHandler.deliver had no guard per target, so one raising output skipped the rest."""

    logger = lab().with_profile("investigator").with_catalyst("ASYNC").build("app.async_guard")
    console = async_handler(logger).targets[0]

    def broken(_record: logging.LogRecord) -> None:
        """An output that always fails."""

        raise RuntimeError("console exploded")

    monkeypatch.setattr(console, "emit", broken)
    logger.warning("still reaches the file")

    assert "still reaches the file" in log_text()
    assert "console exploded" in capsys.readouterr().err


def test_releasing_writes_what_was_queued_then_frees_the_file():
    """Clearing an async logger writes its queued records, then releases the shared file."""

    logger = lab().with_output("file").with_catalyst("ASYNC").build("app.async")
    target = async_handler(logger).targets[0]

    for n in range(200):
        logger.info("last words %d", n)

    clear_handlers(logger)

    assert isinstance(target, logging.FileHandler) and target.stream is None
    assert SHARED_FILES == {}
    assert "last words 199" in Path("logs/app.log").read_text(encoding="utf-8")


def test_releasing_waits_at_most_drain_timeout_for_a_stuck_subscriber(monkeypatch):
    """KN-36: releasing waited forever behind a subscriber that never returned. Now it gives up after DRAIN_TIMEOUT."""

    monkeypatch.setattr(dispatch, "DRAIN_TIMEOUT", 0.2)
    stuck = threading.Event()
    logger = (
        lab().with_output("file").with_catalyst("ASYNC")
        .with_subscriber(lambda record: stuck.wait(10)).build("app.stuck")
    )

    logger.info("held up")
    started = time.monotonic()
    clear_handlers(logger)
    waited = time.monotonic() - started

    stuck.set()

    assert drain(5)
    assert waited < 2


def test_exit_does_not_hang_on_a_stuck_subscriber(tmp_path):
    """KN-36: exit waited as long as the subscriber hung. Now it waits at most DRAIN_TIMEOUT."""

    script = textwrap.dedent("""
        import time
        from logger_lab import lab
        from logger_lab.logging_kernel import dispatch

        dispatch.DRAIN_TIMEOUT = 0.5
        builder = lab().with_output("file").with_catalyst("ASYNC").with_subscriber(lambda r: time.sleep(30))
        builder.build("stuck").warning("x")
    """)
    started = time.monotonic()

    subprocess.run([sys.executable, "-c", script], cwd=tmp_path, timeout=20, check=True)

    assert time.monotonic() - started < 10


def test_drain_from_the_worker_does_not_wait_on_itself():
    """A subscriber calling drain() (on the worker) returns at once instead of deadlocking."""

    results: list[bool] = []
    logger = (
        lab().with_output("console").with_catalyst("ASYNC")
        .with_subscriber(lambda record: results.append(drain())).build("app.async")
    )

    logger.info("call drain from inside")

    assert drain(5)
    assert results == [False]


def test_the_worker_restarts_after_being_stopped():
    """stop_worker() (run at exit) drains and stops. The next record starts a fresh worker."""

    logger = lab().with_output("file").with_catalyst("ASYNC").build("app.async")
    logger.info("before stop")
    stop_worker()

    assert dispatch.worker is None

    logger.info("after stop")
    text = log_text()

    assert "before stop" in text and "after stop" in text
    assert dispatch.worker is not None and dispatch.worker.is_alive()


def test_a_timed_out_stop_never_leaves_two_workers_or_a_lost_record():
    """
    KN-38: after stop_worker() gave up on a stuck worker, a second one started beside it.

    The new worker also ate the stop marker meant for the old one and died, so a lone record
    logged after the stop was never delivered.
    """

    stuck = threading.Event()
    seen: list[tuple[str, int | None]] = []

    def subscriber(record: logging.LogRecord) -> None:
        """Hold up the first record until released, and note which thread delivered each one."""

        if record.getMessage() == "first":
            stuck.wait(10)

        seen.append((record.getMessage(), threading.current_thread().ident))

    logger = lab().with_output("console").with_catalyst("ASYNC").with_subscriber(subscriber).build("app.restart")
    logger.info("first")
    time.sleep(0.2)  # let the worker take "first" and get stuck in it
    stop_worker(timeout=0.2)

    logger.info("second")
    stuck.set()

    assert drain(5)  # "second" is delivered, not left behind a dead worker

    deadline = time.monotonic() + 5
    while [t.name for t in threading.enumerate()].count(dispatch.WORKER_NAME) > 1 and time.monotonic() < deadline:
        time.sleep(0.05)  # the replaced worker finishes "first", then exits

    assert [t.name for t in threading.enumerate()].count(dispatch.WORKER_NAME) == 1
    assert [message for message, _ in seen] == ["first", "second"]
    assert seen[0][1] != seen[1][1]  # the new worker delivered what came after the stop


def test_a_bad_format_call_on_an_async_logger_is_reported_not_raised(capsys):
    """KN-40: merging the message for the queue raised TypeError out of logger.info() and crashed the caller."""

    logger = lab().with_output("file").with_catalyst("ASYNC").build("app.bad_format")

    logger.info("%d", "not a number")
    logger.info("still logging")

    assert "Logging error" in capsys.readouterr().err
    assert "still logging" in log_text()
