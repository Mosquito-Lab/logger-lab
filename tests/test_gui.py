"""The GUI profile, used the way LabFrame's feedback channels use it."""

import logging
import threading
from pathlib import Path

from logger_lab import drain, lab
from logger_lab.logging_kernel import AsyncHandler, LabFileHandler, dispatch
from logger_lab.outputs.relay import RelayHandler


def feedback_logger(subscriber=None) -> logging.Logger:
    """Build ``LabFrame.feedback`` the way LabFrame will: gui profile, one subscriber, its own log dir."""

    builder = lab().with_profile("gui").with_output("file", log_dir="user_logs")

    return (builder.with_subscriber(subscriber) if subscriber else builder).build("LabFrame.feedback")


def test_gui_is_a_rotating_file_and_relay_behind_async_and_works_without_subscribers():
    """One AsyncHandler wraps the rotating file and the relay. No console. With no subscriber yet, just the file."""

    (handler,) = feedback_logger(print).handlers

    assert isinstance(handler, AsyncHandler)
    assert [type(t) for t in handler.targets] == [LabFileHandler, RelayHandler]

    quiet = feedback_logger()
    (handler,) = quiet.handlers
    quiet.warning("nobody listening")

    assert drain(5)
    assert isinstance(handler, AsyncHandler) and [type(t) for t in handler.targets] == [LabFileHandler]
    assert "nobody listening" in Path("user_logs/app.log").read_text(encoding="utf-8")


def test_child_channel_records_reach_file_and_subscriber_off_the_caller_thread(capsys):
    """
    A child channel logger propagates to the feedback logger.

    The subscriber runs on the worker, and nothing reaches stdout.
    """

    seen: list[tuple[str, str, str]] = []
    feedback_logger(lambda r: seen.append((r.name, r.getMessage(), threading.current_thread().name)))

    logging.getLogger("LabFrame.feedback.ProblemsChannel").error("download failed")

    assert drain(5)
    assert seen == [("LabFrame.feedback.ProblemsChannel", "download failed", dispatch.WORKER_NAME)]
    assert "download failed" in Path("user_logs/app.log").read_text(encoding="utf-8")
    assert capsys.readouterr().out == ""


def test_logging_from_many_threads_reaches_the_subscriber_once_each_in_order():
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
        assert [int(m.split()[-1]) for m in seen if m.startswith(f"job {i} ")] == list(range(200))
