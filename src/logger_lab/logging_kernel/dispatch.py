"""
Asynchronous dispatch: one queue and one worker thread for the whole process.

A logger built with the ``ASYNC`` catalyst holds a single `AsyncHandler`. Its `emit()`
freezes the record's message on the calling thread, puts it on the queue and returns. The
worker thread then formats and writes it to the logger's real outputs. So a
``logger.info()`` on a GUI thread never waits on the disk.

Why not the stdlib `QueueHandler` / `QueueListener`:

* `QueueHandler.prepare()` strips ``exc_info`` and ``stack_info`` from every record, so
  Rich tracebacks and logged exceptions would be lost;
* each `QueueListener` serves one fixed set of handlers on its own thread, so every module
  logger would need a thread of its own.

Thread-safe throughout. Records keep their order, because there is one FIFO queue. The
worker is a daemon thread started on first use. At interpreter exit it is drained and
stopped *before* `logging.shutdown()` closes the handlers, so nothing queued is lost.
"""

import atexit
import copy
import logging
import queue
import threading
import time
import weakref
from dataclasses import dataclass

from logger_lab.logging_kernel.handlers import release_handler

DRAIN_TIMEOUT = 5.0  # Seconds to wait for queued records, at exit or when an async logger is released
WORKER_NAME = "logger-lab-dispatch"  # Thread name of the dispatch worker, as seen in tracebacks


@dataclass(frozen=True)
class Stop:
    """A queue item that stops the worker of one *generation*. A newer worker skips it."""

    generation: int


################
# Shared state #
################

# The queue holds (handler, record) pairs to deliver, and Stop markers.
DISPATCH_QUEUE: "queue.SimpleQueue[tuple[AsyncHandler, logging.LogRecord] | Stop]" = queue.SimpleQueue()
pending = 0                              # Records queued but not yet delivered; drain() waits for zero
pending_changed = threading.Condition()  # Guards `pending` and each handler's `queued`, and wakes waiters
worker: threading.Thread | None = None   # The current worker, started on first use by ensure_worker()
worker_lock = threading.Lock()           # Held for every start and a whole stop, so none happens mid-stop
generation = 0                           # Counts the workers started. An older worker is stale and exits
exit_hook_registered = False             # Whether stop_worker() is registered with atexit yet
ON_WORKER = threading.local()            # Its .active is True on every worker thread, stale ones too
SUBSCRIBER_CALL = threading.local()      # Its .active is True while a relay subscriber runs on this thread
ECHOES: "weakref.WeakSet[logging.LogRecord]" = weakref.WeakSet()  # Queued records logged inside a subscriber
ECHOES_LOCK = threading.Lock()           # Guards ECHOES across the threads that queue and deliver


##########
# Worker #
##########

def run_worker(born: int) -> None:
    """
    Deliver queued records until told to stop, or until a newer worker replaces this one.

    *born* is this worker's generation. It stops on its own `Stop` marker and skips an older
    one. A worker replaced while stuck (`stop_worker` timed out) finishes its record and
    exits, so two workers never take records at once (KN-38).
    """

    global pending

    ON_WORKER.active = True

    while True:
        item = DISPATCH_QUEUE.get()

        if isinstance(item, Stop):
            if item.generation == born:
                return

            continue  # A marker for an older worker that never got to it

        handler, record = item

        try:
            handler.deliver(record)  # Never raises: it reports each output's failure itself

        finally:
            with pending_changed:
                pending -= 1
                handler.queued -= 1

                if pending == 0 or handler.queued == 0:  # drain() and AsyncHandler.close() wait on these
                    pending_changed.notify_all()

        if born != generation:  # Replaced while delivering: leave the queue to the new worker
            return


def ensure_worker() -> None:
    """Start a worker if none is running, and register the exit drain once."""

    global worker, exit_hook_registered, generation

    running = worker  # The fast path takes no lock: it runs on every record, and a worker is nearly always up

    if running is not None and running.is_alive():
        return

    with worker_lock:
        running = worker

        if running is not None and running.is_alive():
            return

        generation += 1
        started = threading.Thread(target=run_worker, args=(generation,), name=WORKER_NAME, daemon=True)
        started.start()
        worker = started

        if not exit_hook_registered:
            # Registered after `logging` registered `shutdown`, so it runs first (atexit is LIFO).
            atexit.register(stop_worker)
            exit_hook_registered = True


def on_worker() -> bool:
    """True on a dispatch worker thread, including one that was replaced and is finishing up."""

    return getattr(ON_WORKER, "active", False)


def drain(timeout: float | None = None) -> bool:
    """
    Wait until every queued record has been written.

    Use it in tests, before exiting on purpose, or before showing a crash report. Called
    from a worker (inside a subscriber, say), it returns at once instead of waiting on itself.

    Args:
        timeout: Seconds to wait at most; ``None`` waits as long as it takes.
    Returns:
        ``True`` if the queue is empty, ``False`` on timeout or when called from a worker.
    Example::
        logger.info("saving"); drain(); assert "saving" in log_path.read_text()
    """

    if on_worker():
        return False

    with pending_changed:
        return pending_changed.wait_for(lambda: pending == 0, timeout)


def stop_worker(timeout: float | None = None) -> None:
    """
    Drain the queue, then stop and join the worker. A later record starts a fresh one.

    It runs at interpreter exit. The drain and the join share one deadline, *timeout*
    (`DRAIN_TIMEOUT` by default), so a stuck subscriber can't hold up the exit for longer.
    Records still queued after that are lost.

    Note: called by hand while other threads log, a record queued in the same moment can
    land behind the `Stop` marker. It is delivered when the next record starts a worker
    (KN-47).
    """

    global worker

    limit = DRAIN_TIMEOUT if timeout is None else timeout
    deadline = time.monotonic() + limit
    drain(limit)

    with worker_lock:
        running, worker = worker, None

        if running is not None and running.is_alive():
            DISPATCH_QUEUE.put(Stop(generation))  # Stops only this worker; a newer one skips it
            running.join(max(0.0, deadline - time.monotonic()))


######################################
# Subscriber echoes (the EX-7 guard) #
######################################

def in_subscriber() -> bool:
    """
    True while a relay subscriber runs on this thread.

    A record logged then is an echo. It still reaches the files and consoles, but it is
    never relayed to subscribers again, so a subscriber that logs can't feed itself.
    """

    return getattr(SUBSCRIBER_CALL, "active", False)


def is_echo(record: logging.LogRecord) -> bool:
    """True when *record* was logged inside a subscriber and queued by ``ASYNC``."""

    with ECHOES_LOCK:
        return record in ECHOES


################
# AsyncHandler #
################

def freeze(record: logging.LogRecord) -> logging.LogRecord:
    """
    Return a copy of *record* whose message is final, safe to format later on another thread.

    The message is merged now, so a mutable argument changed after the call can't change the
    log line. ``exc_info`` and ``stack_info`` are kept, unlike the stdlib's `QueueHandler`.
    The copy leaves the original untouched for any other handler on the logger.

    Raises:
        Whatever merging the message raises, such as `TypeError` for ``("%d", "x")``.
        `AsyncHandler.emit` reports it instead.
    """

    frozen = copy.copy(record)
    frozen.msg = record.getMessage()
    frozen.args = None

    return frozen


class AsyncHandler(logging.Handler):
    """
    The one handler on an ``ASYNC`` logger: it queues records for the worker to deliver.

    It owns its *targets* (the logger's real outputs). It delivers to them on the worker
    thread, and releases them when it is released itself.
    """

    def __init__(self, targets: list[logging.Handler], logger_name: str | None = None) -> None:
        """Wrap *targets* for *logger_name*. The handler itself has no level (``NOTSET``)."""

        super().__init__()
        self.targets = tuple(targets)
        self.logger_name = logger_name
        self.closed_for_good = False
        self.queued = 0  # This handler's records still on the queue, guarded by pending_changed

    def emit(self, record: logging.LogRecord) -> None:
        """
        Queue a frozen copy of *record* and return at once. Once closed, the handler drops it.

        A record whose message can't be merged (a bad format call) is reported through
        `handleError`, like every stdlib handler does, instead of raising into the caller (KN-40).
        """

        global pending

        if self.closed_for_good:
            return

        # noinspection PyBroadException
        try:
            frozen = freeze(record)

        except Exception:  # Any error merging the message: a logging call must never raise
            self.handleError(record)
            return

        if in_subscriber():  # Delivered later, outside the subscriber, so remember it is an echo
            with ECHOES_LOCK:
                ECHOES.add(frozen)

        with pending_changed:
            pending += 1
            self.queued += 1

        ensure_worker()
        DISPATCH_QUEUE.put((self, frozen))

    def deliver(self, record: logging.LogRecord) -> None:
        """
        On the worker: hand *record* to every target whose level lets it through.

        Each target is guarded on its own. A target that raises is reported through its
        `handleError`, and the targets after it still get the record. So this never raises.
        """

        for target in self.targets:
            if record.levelno < target.level:
                continue

            # noinspection PyBroadException
            try:
                target.handle(record)

            except Exception:  # Any output error: one failing output must not cost the others the record
                target.handleError(record)

    def close(self) -> None:
        """
        Wait for this handler's queued records, then release the targets (shared files stay counted).

        It waits at most `DRAIN_TIMEOUT`, and not at all once the worker has stopped (at exit)
        or when called on a worker. Records still queued after that are dropped by the
        released targets, so a stuck subscriber can't hang a rebuild or the exit.
        """

        self.closed_for_good = True

        if worker is not None and not on_worker():
            with pending_changed:
                pending_changed.wait_for(lambda: self.queued == 0, DRAIN_TIMEOUT)

        for target in self.targets:
            release_handler(target, self.logger_name)

        super().close()
