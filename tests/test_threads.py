"""D-9: experiments, profiles and the builder are safe to use from many threads at once."""

import logging
import re
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from logger_lab import lab
from logger_lab.logging_kernel import SHARED_FILES

THREADS = 8
RECORDS = 400
LINE = re.compile(r"^\S+ \S+ - app\.worker\d+ - INFO - work:\d+ - worker (\d+) record (\d+)$")


def run_together(count: int, target) -> None:
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


def test_concurrent_builds_open_the_file_once():
    """Eight threads building module loggers at the same moment all get the one shared handler."""

    loggers: dict[int, logging.Logger] = {}

    def build(i: int) -> None:
        """Build one module logger."""

        loggers[i] = lab().with_profile("conspiracy_theorist").build(f"app.worker{i}")

    run_together(THREADS, build)

    file_handlers = {id(lg.handlers[1]) for lg in loggers.values()}

    assert len(file_handlers) == 1
    assert len(SHARED_FILES) == 1 and sum(next(iter(SHARED_FILES.values())).owners.values()) == THREADS


def test_many_threads_rotate_one_file_without_losing_a_line(capsys):
    """Every record from every thread lands whole, exactly once, across rotations — and no WinError 32."""

    def work(i: int) -> None:
        """Log RECORDS lines from module logger *i*."""

        logger = lab().with_experiment("ROTATING").with_file_args(max_bytes=20_000, backup_count=100).build(f"app.worker{i}")

        for n in range(RECORDS):
            logger.info("worker %d record %d", i, n)

    run_together(THREADS, work)

    lines = written_lines(Path("logs"))
    parsed = [LINE.match(line) for line in lines]

    assert all(parsed), [line for line, m in zip(lines, parsed) if not m][:3]  # no torn or merged lines
    assert sorted((int(m.group(1)), int(m.group(2))) for m in parsed if m) == [
        (i, n) for i in range(THREADS) for n in range(RECORDS)
    ]
    assert len(list(Path("logs").glob("app.log.*"))) > 1  # it really rotated
    assert "PermissionError" not in capsys.readouterr().err


def test_rebuilding_while_other_threads_log():
    """CR-10: rebuilding a logger mid-traffic never errors, never loses a handler, never leaks a file."""

    lab().with_profile("investigator").build("app.busy")
    stop = threading.Event()
    errors: list[BaseException] = []

    def log_forever() -> None:
        """Log to app.busy until told to stop."""

        logger = logging.getLogger("app.busy")

        try:
            while not stop.is_set():
                logger.info("tick")

        except BaseException as err:  # surface to the main thread
            errors.append(err)

    workers = [threading.Thread(target=log_forever) for _ in range(4)]

    for worker in workers:
        worker.start()

    for i in range(50):
        profile = "investigator" if i % 2 else "conspiracy_theorist"  # alternate FILE ↔ ROTATING on one path
        lab().with_profile(profile).build("app.busy")

    stop.set()

    for worker in workers:
        worker.join()

    assert errors == []
    assert len(logging.getLogger("app.busy").handlers) == 2
    assert len(SHARED_FILES) == 1  # every replaced handler was released, not leaked
