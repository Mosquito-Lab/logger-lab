"""Helpers shared by the test files: threads that start together, and reading what a logger wrote."""

import logging
import threading
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from logger_lab.logging_kernel import LabFileHandler


def run_together(count: int, target: Callable[[int], object]) -> None:
    """Start *count* threads on *target(i)* at the same moment and wait for all of them."""

    barrier = threading.Barrier(count)

    def start(i: int) -> None:
        """Wait for every thread, then run."""

        barrier.wait()
        target(i)

    with ThreadPoolExecutor(max_workers=count) as pool:
        for future in [pool.submit(start, i) for i in range(count)]:
            future.result()  # re-raise anything a thread hit


def written_lines(log_dir: Path) -> list[str]:
    """Return every line in ``app.log`` and its rotated copies."""

    return [line for path in sorted(log_dir.glob("app.log*")) for line in path.read_text(encoding="utf-8").splitlines()]


def file_handler(logger: logging.Logger) -> LabFileHandler:
    """Return *logger*'s one file handler, looking inside an `AsyncHandler` too."""

    handlers = [target for handler in logger.handlers for target in getattr(handler, "targets", [handler])]
    (handler,) = [h for h in handlers if isinstance(h, LabFileHandler)]

    return handler
