"""
Asynchronous dispatch: one queue and one worker thread for the whole process.

A logger built with the ``async`` experiment holds a single `AsyncHandler`.  Its `emit()`
freezes the record's message on the calling thread, puts it on the queue and returns; the
worker thread formats and writes it to the logger's real outputs.  So a ``logger.info()``
on a GUI thread never waits on the disk.

Why not the stdlib `QueueHandler` / `QueueListener`:

* `QueueHandler.prepare()` strips ``exc_info`` and ``stack_info`` from every record, so
  Rich tracebacks and logged exceptions would be lost;
* each `QueueListener` serves one fixed set of handlers on its own thread, so every module
  logger would need a thread of its own.

Thread-safe throughout.  Records keep their order (one FIFO queue).  The worker is a daemon
thread started on first use; at interpreter exit it is drained and stopped *before*
`logging.shutdown()` closes the handlers, so nothing queued is lost.
"""

import atexit
import copy
import logging
import queue
import threading
from typing import Callable

from logger_lab.logging_kernel.handlers import release_handler

EXIT_DRAIN_TIMEOUT = 5.0  # Seconds to wait at interpreter exit for queued records to be written
WORKER_NAME = "logger-lab-dispatch"  # Thread name of the dispatch worker — visible in tracebacks and tests


##############
# Dispatcher #
##############

DISPATCHERS: set[Callable[..., list[logging.Handler]]] = set()  # Factories marked with @dispatcher


def dispatcher(factory: Callable[..., list[logging.Handler]]) -> Callable[..., list[logging.Handler]]:
    """
    Mark *factory* as a dispatcher: it receives the logger's built outputs as ``handlers=``
    and returns the handlers that go on the logger in their place.

    The builder and `build_profile` call a dispatcher last.  It must be registered on the
    ``DISPATCH`` channel, so a logger has at most one.

    Example::
        @dispatcher
        def async_experiment(level, *, handlers, logger_name=None, **kwargs): ...
    """

    DISPATCHERS.add(factory)

    return factory


def is_dispatcher(factory: object) -> bool:
    """Return whether *factory* was marked with `dispatcher`."""

    return factory in DISPATCHERS


##################
# Queue + worker #
##################

DISPATCH_QUEUE: "queue.SimpleQueue[tuple[AsyncHandler, logging.LogRecord] | None]" = queue.SimpleQueue()  # None stops the worker
pending = 0                              # Records queued but not yet delivered; drain() waits for zero
pending_changed = threading.Condition()  # Guards `pending` and wakes drain()
worker: threading.Thread | None = None   # The dispatch worker, started lazily by ensure_worker()
worker_lock = threading.Lock()           # Held for every start and a whole stop: no new worker mid-stop
exit_hook_registered = False             # Whether stop_worker() is registered with atexit yet


def run_worker() -> None:
    """Deliver queued records until the stop sentinel (``None``) arrives."""

    global pending

    while True:
        item = DISPATCH_QUEUE.get()

        if item is None:
            return

        handler, record = item

        try:
            handler.deliver(record)

        except Exception:  # an output must never kill the worker — report it like logging does
            handler.handleError(record)

        finally:
            with pending_changed:
                pending -= 1

                if pending == 0:
                    pending_changed.notify_all()


def ensure_worker() -> None:
    """Start the worker thread if it isn't running, registering its exit drain once."""

    global worker, exit_hook_registered

    running = worker  # fast path, no lock: called on every record, and the worker is almost always up

    if running is not None and running.is_alive():
        return

    with worker_lock:
        if worker is not None and worker.is_alive():
            return

        worker = threading.Thread(target=run_worker, name=WORKER_NAME, daemon=True)
        worker.start()

        if not exit_hook_registered:
            # Registered after `logging` registered `shutdown`, so it runs first (atexit is LIFO).
            atexit.register(stop_worker)
            exit_hook_registered = True


def drain(timeout: float | None = None) -> bool:
    """
    Wait until every queued record has been written.

    Use it in tests, before exiting on purpose, or before showing a crash report.  Called
    from the worker thread itself (e.g. inside a subscriber), it returns at once instead of
    waiting on itself.

    Args:
        timeout: Seconds to wait at most; ``None`` waits as long as it takes.
    Returns:
        ``True`` if the queue is empty, ``False`` on timeout (or when called from the worker).
    Example::
        logger.info("saving"); drain(); assert "saving" in log_path.read_text()
    """

    if threading.current_thread() is worker:
        return False

    with pending_changed:
        return pending_changed.wait_for(lambda: pending == 0, timeout)


def stop_worker(timeout: float = EXIT_DRAIN_TIMEOUT) -> None:
    """Drain the queue, then stop and join the worker.  A later record starts a fresh one."""

    global worker

    drain(timeout)

    with worker_lock:  # held through the join: the stop sentinel can only reach *this* worker
        running, worker = worker, None

        if running is not None and running.is_alive():
            DISPATCH_QUEUE.put(None)
            running.join(timeout)


################
# AsyncHandler #
################

def freeze(record: logging.LogRecord) -> logging.LogRecord:
    """
    Return a copy of *record* whose message is final, safe to format later on another thread.

    The message is merged now, so a mutable argument changed after the call can't change the
    log line.  ``exc_info`` and ``stack_info`` are kept, unlike the stdlib's `QueueHandler`.
    The copy leaves the original untouched for any other handler on the logger.
    """

    frozen = copy.copy(record)
    frozen.msg = record.getMessage()
    frozen.args = None

    return frozen


class AsyncHandler(logging.Handler):
    """
    The one handler on an ``async`` logger: queues records for the worker to deliver.

    It owns its *targets* (the logger's real outputs): delivering to them on the worker
    thread, and releasing them when it is itself released.
    """

    def __init__(self, targets: list[logging.Handler], logger_name: str | None = None) -> None:
        """Wrap *targets* for *logger_name*; the handler itself has no level (``NOTSET``)."""

        super().__init__()
        self.targets = tuple(targets)
        self.logger_name = logger_name
        self.closed_for_good = False

    def emit(self, record: logging.LogRecord) -> None:
        """Queue a frozen copy of *record* and return at once; dropped once the handler is closed."""

        global pending

        if self.closed_for_good:
            return

        frozen = freeze(record)

        with pending_changed:
            pending += 1

        ensure_worker()
        DISPATCH_QUEUE.put((self, frozen))

    def deliver(self, record: logging.LogRecord) -> None:
        """On the worker: hand *record* to every target whose level lets it through."""

        for target in self.targets:
            if record.levelno >= target.level:
                target.handle(record)

    def close(self) -> None:
        """Wait for this logger's queued records, then release the targets (shared files stay counted)."""

        self.closed_for_good = True
        drain()

        for target in self.targets:
            release_handler(target, self.logger_name)

        super().close()
