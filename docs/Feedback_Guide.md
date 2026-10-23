# Feedback Guide: async, live subscribers and Qt

logger-lab isn't only a debugging tool. Every record is a piece of **feedback**,
and a logger decides who receives it:

| Who receives it | Building blocks | Typical use |
| --- | --- | --- |
| A person at a terminal | the `console` output (`RICH`, `TEXT`; `MINIMAL` / `VERBOSE`) | Development, CLI tools |
| Whoever reads the logs later | the `file` output (`TEXT`; `ROTATING`, `TIMED`) | Support, audits, post-mortems |
| A machine | the `JSON` format, on the console or a file | Pipelines, aggregators, LLM tooling |
| A live UI or service | the `relay` output + `with_subscriber()` | GUIs (Qt), dashboards, alerts, tests |
| (no audience) | the `ASYNC` catalyst | Decides *how* records reach the others: off the calling thread |

One logger can serve several of these at once: one output of each kind, and
as many subscribers as you like.

This guide covers the last two rows: how `ASYNC` works, how subscribers work,
and how to connect them to Qt and to other event loops. The API details are
in `API_Reference.md`, and the rules they follow are in
`Standards_and_Tracker.md`.

---

## 1. How a record travels

### Without `ASYNC`

```text
logger.info("saved")                      ← your thread
  └─ level check (the logger's level)
  └─ for each handler on the logger:      ← still your thread
        file   → format + write to disk
        relay  → call each subscriber
        console→ format + print
```

Everything runs on the thread that logged. That's simple and immediate, and
it means a slow disk or a slow subscriber slows the caller down.

### With `ASYNC`

```text
logger.info("saved")                      ← your thread
  └─ level check
  └─ AsyncHandler.emit
        freeze the record (the message is final, the traceback is kept)
        put it on the dispatch queue       ← returns here; your thread moves on
                ⋮
dispatch worker ("logger-lab-dispatch")   ← one thread for the whole process
  └─ takes records off the queue, in order
  └─ for each output: file → write · relay → subscribers · console → print
```

The builder hands every output's handlers to the `ASYNC` catalyst, so the
logger itself holds a single `AsyncHandler`:

```python
from logger_lab import lab

logger = lab().with_profile("investigator").with_catalyst("ASYNC").build(__name__)
# logger.handlers == [AsyncHandler]   →  .targets == [LabRichHandler, LabFileHandler]
```

---

## 2. What `ASYNC` guarantees

| Guarantee | How |
| --- | --- |
| **The caller never waits on a slow disk or subscriber** | `emit()` only freezes the record and queues it. (Measured on Windows, 2026-10-23: about 25 µs → 13 µs per written file record, on the calling thread.) |
| **Order is kept** | One FIFO queue and one worker. Records come out in the order they went in, across all async loggers. |
| **The line is fixed when you log** | The message is merged with its arguments on your thread, so changing a list after `logger.info("%s", items)` can't change the line. |
| **Tracebacks survive** | `exc_info` and `stack_info` travel with the record (the stdlib `QueueHandler` drops them), so `logger.exception()` still writes the traceback, and the JSON still has `"exception"`. |
| **Nothing queued is lost at a normal exit** | At interpreter exit the worker is drained and stopped *before* `logging.shutdown()` closes the files. That takes 5 s at most (`DRAIN_TIMEOUT`), so a stuck subscriber can't hang the exit. |
| **Rebuilding a logger is safe** | Releasing an `AsyncHandler` waits for *its own* queued records (5 s at most), then releases its outputs, so shared files keep the right count. |
| **One worker, however many loggers** | Thirty module loggers with `ASYNC` still share one thread. |
| **Thread-safe** | Log from any number of threads. |

### `drain()`: wait for the queue

```python
from logger_lab import drain

logger.error("about to crash-report")
drain()             # waits until everything queued has been written
drain(timeout=2.0)  # True if the queue emptied, False on timeout
```

Use it in tests, before showing a crash dialog, or before exiting on purpose.
If you call it from the worker itself (inside a subscriber), it returns
`False` at once instead of waiting on itself.

---

## 3. Limits to design around

These were measured, not guessed (2026-10-22).

| Limit | What happens | What to do |
| --- | --- | --- |
| **One slow output delays all async logging** | There is one worker. A subscriber that takes 200 ms made a record on an *unrelated* async logger wait about 212 ms. | Keep subscribers fast: hand the record to your own queue or signal and return. Never do I/O, network or UI work inside the subscriber. |
| **A record logged inside a subscriber is not relayed** | Such a record (an echo) still reaches files and consoles. But no subscriber gets it, on any logger, so a subscriber that logs can't feed itself. This holds with and without `ASYNC` (`EX-7`, fixed 2026-10-23). | Nothing, usually. If a subscriber must notify another subscriber, call it directly instead of logging. |
| **Context variables don't reach the worker** | A `contextvars` value read by a filter on an *output* is the worker's (empty); read by a filter on the *logger* it's the caller's. | Stamp context onto the record with a **logger-level** filter (`logger.addFilter(...)`), which runs on the caller. The `TRACE` theory must do the same. |
| **The queue is unbounded** | A subscriber slower than your logging rate grows memory. | Same as the first row: fast subscribers. (A capped queue with a drop count is a later option, D-14.) |
| **One process only** | Several processes writing one file aren't coordinated. | One log file per process for now; process safety is on the roadmap. |
| **Killed processes lose the queue** | `atexit` doesn't run on a hard kill or a crash in native code. | `drain()` at the points that matter (before a crash report, on quit). |

---

## 4. Live subscribers (`relay`)

```python
import logging
from logger_lab import lab

alerts: list[logging.LogRecord] = []

logger = (
    lab()
    .with_output("console")
    .with_subscriber(alerts.append, level="ERROR")   # only ERROR and above
    .with_subscriber(print)                          # everything the logger lets through
    .build(__name__)
)
```

| Rule | Detail |
| --- | --- |
| `with_subscriber` brings `relay` | No need to add the `relay` output yourself. |
| One handler per subscriber | Each one has its own level. `level=None` means the logger's level decides. |
| The callback gets the `LogRecord` | It's shared with the other outputs, so **treat it as read-only**. Format it with a `logging.Formatter` if you need text. |
| Which thread | **With `ASYNC`: the dispatch worker. Without: whichever thread logged.** |
| A callback that raises | It's reported like any handler error (to stderr) and never stops logging or the other subscribers. |
| Child loggers | Records from `logging.getLogger("app.sub")` propagate into the `app` logger's subscribers. |

---

## 5. Qt (PySide6 / PyQt)

Subscribers know nothing about Qt. The bridge is one line: pass a **signal's
`emit`** as the subscriber.

```python
from PySide6.QtCore import QObject, Signal
from logger_lab import lab

class LogRelay(QObject):
    record_logged = Signal(object)        # PyQt: pyqtSignal(object)

relay = LogRelay()                        # created on the GUI thread

logger = (
    lab()
    .with_profile("gui")                  # file + ROTATING + relay + ASYNC, no console
    .with_subscriber(relay.record_logged.emit)
    .with_output("file", log_dir=user_log_dir)   # a writable per-user directory
    .with_level("DEBUG")
    .build("my_app")
)

relay.record_logged.connect(problems_view.add_record)   # runs on the GUI thread
```

**Why this is safe.** The subscriber runs on the dispatch worker. But Qt
delivers an `emit` from a non-GUI thread through a queued connection, on the
**receiver's** thread, which is the GUI thread. So your slot can touch widgets.
We verified this with real PySide6. A record logged on a worker thread and one
logged on the GUI thread both reached the slot on the GUI thread, and the file.

**In the slot,** turn the record into text on the GUI thread:

```python
formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")

def add_record(record: logging.LogRecord) -> None:
    item = formatter.format(record)       # includes the traceback when there is one
    ...
```

**Modules and jobs.** Every module logs to its own child logger
(`logging.getLogger("my_app.downloads")`), and the records propagate into
`my_app`: the file, the GUI and nothing else to configure. Job threads (a
`QThread`, `threading.Thread`, or LabFrame's `JobWorker`) log as usual; the
GUI thread never waits on them.

**Windowed builds** (`pythonw`, PyInstaller `--windowed`) have no stdout or
stderr, which is why `gui` has no console output.

**On quit,** queued records are written at exit automatically. Call `drain()`
in `aboutToQuit` if you want them on disk before your own shutdown code runs.

### LabFrame

LabFrame's feedback channels log through child loggers of
`LabFrame.feedback`. With 0.2.0, `LabFrame/feedback/channel.py` becomes:

```python
feedback_logger = (
    lab().with_profile("gui")
    .with_subscriber(feedback_log_relay.record_logged.emit)
    .with_output("file", log_dir=app_log_dir)
    .with_level("DEBUG")                  # LabFrame's channels log at DEBUG
    .build("LabFrame.feedback")
)
```

`QtRelayHandler` goes away. `FeedbackLogRelay` and every channel stay as they
are (`Continuation.md` §5).

---

## 6. Other event loops and consumers

The subscriber always runs on a thread that isn't yours (with `ASYNC`), so
hand the record over in whatever way your loop accepts from another thread.

**asyncio** (web sockets, dashboards):

```python
import asyncio, logging

def asyncio_subscriber(loop: asyncio.AbstractEventLoop, queue: asyncio.Queue):
    """Return a subscriber that hands records to *queue* on *loop*'s thread."""

    return lambda record: loop.call_soon_threadsafe(queue.put_nowait, record)

# inside the running loop:
records: asyncio.Queue[logging.LogRecord] = asyncio.Queue()
logger = lab().with_catalyst("ASYNC").with_subscriber(
    asyncio_subscriber(asyncio.get_running_loop(), records)).build("service")
```

**Tkinter** (no thread-safe signal, so poll a queue):

```python
import queue

inbox: "queue.Queue[logging.LogRecord]" = queue.Queue()
logger = lab().with_profile("gui").with_subscriber(inbox.put).build("tk_app")

def pump() -> None:
    while not inbox.empty():
        show(inbox.get_nowait())
    root.after(100, pump)                 # every 100 ms, on Tk's thread

pump()
```

**Tests** collect records directly:

```python
seen: list[str] = []
logger = lab().with_catalyst("ASYNC").with_subscriber(lambda r: seen.append(r.getMessage())).build("t")
logger.info("hello")
drain()
assert seen == ["hello"]
```

---

## 7. Checklist

- [ ] Subscribers return quickly and hand the record to a signal, queue or
      loop. No I/O inside.
- [ ] Subscribers don't rely on their own log lines reaching other subscribers
      (echoes are never relayed).
- [ ] Context (job IDs, request IDs) is stamped by a **logger-level** filter.
- [ ] GUI apps use `gui` (no console) and a writable `log_dir`.
- [ ] Set `with_level("DEBUG")` if your feedback includes DEBUG records (the
      default is INFO).
- [ ] `drain()` before crash reports or deliberate exits that must not lose
      records.
- [ ] One process per log file (process safety isn't covered yet).

## 8. What's coming

These are tracked in `Continuation.md`:
- **Correlation IDs** (`TRACE`): group feedback by job or request.
- **Lifecycle events**: started, progress, done and failed, as a standard
  shape UIs can drive straight from.
- **Rate limiting** for subscribers.
- **Process safety.**
