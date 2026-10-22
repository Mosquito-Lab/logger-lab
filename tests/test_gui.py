"""The GUI profile, used the way LabFrame's feedback channels use it."""

import logging
import threading
from pathlib import Path

from logger_lab import drain, lab
from logger_lab.logging_kernel import AsyncHandler, SharedRotatingFileHandler, dispatch
from logger_lab.experiments.relay import RelayHandler
from logger_lab.profiles import gui


def feedback_logger(subscriber) -> logging.Logger:
    """Build ``LabFrame.feedback`` the way LabFrame will: gui profile, one subscriber, its own log dir."""

    return lab().with_profile("gui").with_subscriber(subscriber).with_file_args(log_dir="user_logs").build("LabFrame.feedback")


def test_gui_is_rotating_file_and_relay_behind_async():
    """One AsyncHandler on the logger, wrapping the rotating file and the relay. No console."""

    logger = feedback_logger(print)
    (handler,) = logger.handlers

    assert isinstance(handler, AsyncHandler)
    assert [type(t) for t in handler.targets] == [SharedRotatingFileHandler, RelayHandler]


def test_child_channel_records_reach_file_and_subscriber_off_the_caller_thread(capsys):
    """A child channel logger propagates to the feedback logger; the subscriber runs on the worker, nothing hits stdout."""

    seen: list[tuple[str, str, str]] = []
    feedback_logger(lambda r: seen.append((r.name, r.getMessage(), threading.current_thread().name)))

    logging.getLogger("LabFrame.feedback.ProblemsChannel").error("download failed")

    assert drain(5)
    assert seen == [("LabFrame.feedback.ProblemsChannel", "download failed", dispatch.WORKER_NAME)]
    assert "download failed" in Path("user_logs/app.log").read_text(encoding="utf-8")
    assert capsys.readouterr().out == ""


def test_logging_from_many_threads_reaches_the_subscriber_once_each():
    """Job worker threads logging at once: every record arrives exactly once, in each thread's order."""

    seen: list[str] = []
    logger = feedback_logger(lambda r: seen.append(r.getMessage()))

    def job(i: int) -> None:
        """One worker thread's log lines."""

        for n in range(200):
            logger.info("job %d step %d", i, n)

    threads = [threading.Thread(target=job, args=(i,)) for i in range(6)]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    assert drain(10)
    assert sorted(seen) == sorted(f"job {i} step {n}" for i in range(6) for n in range(200))

    for i in range(6):
        steps = [int(m.split()[-1]) for m in seen if m.startswith(f"job {i} ")]
        assert steps == list(range(200))


def test_direct_call_takes_subscribers_too():
    """gui(name, subscribers=...) builds the same shape without the builder."""

    seen: list[str] = []
    logger = gui("direct.gui", subscribers=((lambda r: seen.append(r.getMessage()), None),))

    logger.warning("direct")

    assert drain(5)
    assert seen == ["direct"]
