"""ASYNC: records are queued on the caller's thread and written on the one dispatch worker."""

import logging
import re
import threading
from pathlib import Path

import pytest

from logger_lab import BuilderError, drain, lab
from logger_lab.logging_kernel import SHARED_FILES, AsyncHandler, clear_handlers, dispatch, stop_worker

THREADS = 8
RECORDS = 400
LINE = re.compile(r"^\S+ \S+ - app\.worker\d+ - INFO - work:\d+ - worker (\d+) record (\d+)$")


def async_handler(logger: logging.Logger) -> AsyncHandler:
    """Return *logger*'s one handler, checked to be the `AsyncHandler`."""

    (handler,) = logger.handlers
    assert isinstance(handler, AsyncHandler)

    return handler


def log_text() -> str:
    """Return ``logs/app.log`` after every queued record is written."""

    assert drain(5)

    return Path("logs/app.log").read_text(encoding="utf-8")


def test_async_logger_holds_one_dispatching_handler():
    """The logger gets a single `AsyncHandler`; its outputs live inside it."""

    logger = lab().with_experiment("FILE").with_experiment("ASYNC").build("app.async")

    assert [type(t).__name__ for t in async_handler(logger).targets] == ["SharedFileHandler"]


def test_records_are_written_by_the_worker_thread():
    """The caller only queues; the dispatch worker does the writing."""

    writers: list[str] = []
    logger = (
        lab().with_experiment("FILE").with_experiment("ASYNC")
        .with_subscriber(lambda record: writers.append(threading.current_thread().name))
        .build("app.async")
    )

    logger.info("queued")

    assert "queued" in log_text()
    assert writers == [dispatch.WORKER_NAME]


def test_tracebacks_survive_the_queue():
    """Unlike the stdlib QueueHandler, exc_info reaches the output, so the traceback is written."""

    logger = lab().with_experiment("FILE").with_experiment("ASYNC").build("app.async")

    try:
        raise ValueError("kaboom")
    except ValueError:
        logger.exception("it broke")

    text = log_text()

    assert "it broke" in text and "Traceback (most recent call last)" in text and "ValueError: kaboom" in text


def test_message_is_frozen_when_logged():
    """A mutable argument changed after the call can't change the line that gets written."""

    logger = lab().with_experiment("FILE").with_experiment("ASYNC").build("app.async")
    payload = ["before"]

    logger.info("payload=%s", payload)
    payload[0] = "after"

    assert "payload=['before']" in log_text()


def test_order_is_kept():
    """One FIFO queue: records come out in the order they went in."""

    logger = lab().with_experiment("FILE").with_experiment("ASYNC").build("app.async")

    for n in range(500):
        logger.info("n=%d", n)

    numbers = [int(m) for m in re.findall(r"n=(\d+)", log_text())]

    assert numbers == list(range(500))


def test_one_worker_for_the_whole_process():
    """Eight threads logging through eight async loggers at the same moment still share one worker thread."""

    loggers = [lab().with_experiment("FILE").with_experiment("ASYNC").build(f"app.w{i}") for i in range(THREADS)]
    barrier = threading.Barrier(THREADS)

    def burst(logger: logging.Logger) -> None:
        """Wait for the others, then log."""

        barrier.wait()

        for n in range(50):
            logger.info("burst %d", n)

    threads = [threading.Thread(target=burst, args=(logger,)) for logger in loggers]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    assert drain(5)
    assert [t.name for t in threading.enumerate()].count(dispatch.WORKER_NAME) == 1


def test_async_needs_an_output():
    """ASYNC on its own would drop everything, so it fails loudly instead."""

    with pytest.raises(BuilderError, match="no output to dispatch to"):
        lab().with_experiment("ASYNC").build("app.lonely")


def test_async_is_built_last_and_once():
    """ASYNC wraps the outputs, so it plans last; queued twice, it is a duplicate (first kept), not two queues."""

    plan = lab().with_experiment("FILE").with_experiment("ASYNC").plan()

    assert plan[-1].value == "ASYNC"

    with pytest.warns(UserWarning, match="queued twice"):
        lab().with_experiment("FILE").with_experiment("ASYNC").with_experiment("ASYNC").build("app.twice")


def test_releasing_waits_for_queued_records_then_frees_the_file():
    """Clearing an async logger writes what was queued, then releases the shared file."""

    logger = lab().with_experiment("FILE").with_experiment("ASYNC").build("app.async")
    target = async_handler(logger).targets[0]

    for n in range(200):
        logger.info("last words %d", n)

    clear_handlers(logger)

    assert isinstance(target, logging.FileHandler) and target.stream is None
    assert SHARED_FILES == {}
    assert "last words 199" in Path("logs/app.log").read_text(encoding="utf-8")


def test_drain_from_the_worker_does_not_wait_on_itself():
    """A subscriber calling drain() (on the worker) returns at once instead of deadlocking."""

    results: list[bool] = []
    logger = lab().with_experiment("ASYNC").with_subscriber(lambda record: results.append(drain())).build("app.async")

    logger.info("call drain from inside")

    assert drain(5)
    assert results == [False]


def test_worker_restarts_after_being_stopped():
    """stop_worker() (run at exit) drains and stops; the next record starts a fresh worker."""

    logger = lab().with_experiment("FILE").with_experiment("ASYNC").build("app.async")
    logger.info("before stop")
    stop_worker()

    assert dispatch.worker is None

    logger.info("after stop")
    text = log_text()

    assert "before stop" in text and "after stop" in text
    assert dispatch.worker is not None and dispatch.worker.is_alive()


def test_many_threads_through_one_async_file():
    """Thread safety (Standards §2.4): 8 threads × 400 records, rotating, every line whole and present once."""

    def work(i: int) -> None:
        """Log RECORDS lines from module logger *i*."""

        logger = (
            lab().with_experiment("ROTATING").with_experiment("ASYNC")
            .with_file_args(max_bytes=20_000, backup_count=100).build(f"app.worker{i}")
        )

        for n in range(RECORDS):
            logger.info("worker %d record %d", i, n)

    barrier = threading.Barrier(THREADS)
    threads = [threading.Thread(target=lambda i=i: (barrier.wait(), work(i))) for i in range(THREADS)]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    assert drain(10)

    lines = [line for path in sorted(Path("logs").glob("app.log*")) for line in path.read_text(encoding="utf-8").splitlines()]
    parsed = [LINE.match(line) for line in lines]

    assert all(parsed)
    assert sorted((int(m.group(1)), int(m.group(2))) for m in parsed if m) == [
        (i, n) for i in range(THREADS) for n in range(RECORDS)
    ]

