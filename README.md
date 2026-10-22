# 🧪 logger-lab

> Logging, reimagined as a system.

`logger-lab` is a composable Python logging toolkit built around a simple idea:

**logging should be modular, readable, and adaptable — for both humans and machines.**

Instead of writing repetitive logging setup, you select from **experiments**, apply **profiles**,
or compose your own logger by assembling them like a system. Every logger it hands back is a plain
`logging.Logger`, so everything that works with the standard library keeps working.

---

## 🚀 Installation

```bash
pip install logger-lab
```

---

## ⚡ Quick Start

```python
from logger_lab import lab

logger = lab().with_profile("investigator").build(__name__)

logger.info("System online")
logger.debug("Inspecting state")   # below the default INFO, so not shown
logger.error("Something broke")
```

`lab()` is the one way to build a logger: queue what you want, then `build(name)`.

### Summary of usage
Every experiment, profile and theory can be picked by its **enum member** or its **value string**
(case-insensitive):

```python
import logging
from logger_lab import lab, ExperimentType

# Profiles (prebuilt combinations):
profile_logger = lab().with_profile("conspiracy_theorist").build("profile_test")

# Experiments (single handler factories):
experiment_logger = lab().with_experiment(ExperimentType.MINIMALIST).build("experiment_test")

# Custom composition — its own file, because profile_logger's
# rotating handler already owns logs/app.log:
built_logger = (
    lab()
    .with_experiment('STANDARD')
    .with_experiment(ExperimentType.FILE)
    .with_file_args(filename="builder.log")
    .with_level(logging.DEBUG)
    .build(__name__)
)
```

> A member's *name* can differ from its *value*. Use the value string:
> `ExperimentType.ROTATING_FILE` is `"ROTATING"`, `ProfileType.AGENT` is `"AI_AGENT"`,
> `ProfileType.CONSPIRATOR` is `"CONSPIRACY_THEORIST"`.

---

## 🧪 Experiments

Experiments are **atomic logging behaviors** — pure functions that return a list of configured handlers.

Each experiment controls exactly one thing: how logs are formatted and where they go — its **channel**.

| Experiment      | Value          | Channel | Handler                  | Description                                       |
|-----------------|----------------|---------|--------------------------|---------------------------------------------------|
| `standard`      | `"STANDARD"`   | console | `RichHandler`            | Colorized console output with traceback support   |
| `minimalist`    | `"MINIMALIST"` | console | `StreamHandler`          | Plain `LEVEL: message` — warnings only by default |
| `verbose`       | `"VERBOSE"`    | console | `StreamHandler`          | Full context: timestamp, module, function, line   |
| `file`          | `"FILE"`       | file    | `FileHandler` (shared)   | Persistent plain-text log at `logs/app.log`       |
| `rotating_file` | `"ROTATING"`   | file    | `RotatingFileHandler` (shared) | Auto-rotates at 5 MiB, keeps 3 backups      |
| `ai`            | `"AI"`         | json    | `StreamHandler` (stderr) | Structured JSON — Mosquito Lab Standard v1.1      |
| `relay`         | `"RELAY"`      | live    | `RelayHandler`           | Every record to your callbacks (`with_subscriber`) |
| `async`         | `"ASYNC"`      | dispatch | `AsyncHandler`          | Not an output: moves the others off the calling thread |

### Using a single experiment

```python
from logger_lab import lab

logger = lab().with_experiment("minimalist").build(__name__)
logger.warning("Ready")   # minimalist defaults to WARNING
```

---

## 🧫 Profiles

Profiles are **prebuilt combinations of experiments** tuned for common use cases.

| Profile               | Value                   | Experiments                | Use case                             |
|-----------------------|-------------------------|----------------------------|--------------------------------------|
| `observer`            | `"OBSERVER"`            | `minimalist`               | Production — warnings and above only |
| `investigator`        | `"INVESTIGATOR"`        | `standard` + `file`        | Development — Rich console + disk    |
| `conspiracy_theorist` | `"CONSPIRACY_THEORIST"` | `verbose` + `rotating_file` | Deep archival — nothing missed      |
| `ai_agent`            | `"AI_AGENT"`            | `ai`                       | Structured JSON for pipelines        |
| `gui`                 | `"GUI"`                 | `rotating_file` + `relay` + `async` | Desktop apps — no console, nothing blocks the GUI thread |

```python
from logger_lab import lab, ProfileType

payload = "super dangerous and malicious payload!"

logger = lab().with_profile(ProfileType.CONSPIRATOR).with_level("DEBUG").build(__name__)
logger.debug("Payload received: %s", payload)
logger.error("Unexpected response", exc_info=True)
```

---

## 🧬 Custom Composition

For full control, build your logger like a system:

```python
from logger_lab import lab, ExperimentType

logger = (
    lab()
    .with_experiment(ExperimentType.MINIMALIST)
    .with_experiment(ExperimentType.FILE)
    .with_level("DEBUG")
    .build(__name__)
)
```

Mix a profile with additional experiments:

```python
from logger_lab import lab, ExperimentType, ProfileType

logger = (
    lab()
    .with_profile(ProfileType.INVESTIGATOR)
    .with_experiment(ExperimentType.AI)
    .with_level("INFO")
    .build(__name__)
)
```

### File args

`with_file_args()` sets where and how file experiments write — for the profile's experiments too:

```python
from logger_lab import lab

logger = (
    lab()
    .with_profile("conspiracy_theorist")
    .with_file_args(log_dir="run_logs", filename="session.log", max_bytes=1_048_576, backup_count=5)
    .build(__name__)
)
```

| Arg            | Default   | Used by                   |
|----------------|-----------|---------------------------|
| `log_dir`      | `logs/`   | `file`, `rotating_file`   |
| `filename`     | `app.log` | `file`, `rotating_file`   |
| `encoding`     | `utf-8`   | `file`, `rotating_file`   |
| `max_bytes`    | 5 MiB     | `rotating_file`           |
| `backup_count` | `3`       | `rotating_file`           |

Calling it again replaces every arg — omitted ones go back to their defaults.

### Composition rules

Experiments are built to work together, so a logger takes **at most one experiment per channel**:
one console, one file, one JSON.

* **Two different experiments on one channel** raise `ExperimentClashError` — `standard` and
  `minimalist` would print every record twice, and `file` and `rotating_file` would fight over the
  same file.
* **The same experiment twice** (often: one a profile already includes) warns with
  `DuplicateExperimentWarning` and only the first is built.

```python
lab().with_profile("investigator").with_experiment("ROTATING").build(__name__)
# ExperimentClashError: 'ROTATING' (queued) clashes with 'FILE' (from profile 'INVESTIGATOR'):
# both write to the FILE channel. A logger takes at most one experiment per channel ...

lab().with_profile("investigator").with_experiment("FILE").build(__name__)
# DuplicateExperimentWarning: 'FILE' is queued twice (from profile 'INVESTIGATOR', then queued)
# — keeping the first and skipping the duplicate.
```

Check a composition without building anything with `plan()`:

```python
lab().with_profile("investigator").with_experiment("AI").plan()
# [ExperimentType.STANDARD, ExperimentType.FILE, ExperimentType.AI]
```

### Many modules, one file

Give every module its own logger (`__name__`) and let each pick its own experiments and level —
they can all write to the same `logs/app.log`. Each log file is opened **once per process**: every
logger writing to it shares one handler, so records never collide and rotation keeps working.

```python
# loaders.py — chatty, file only
logger = lab().with_experiment("ROTATING").with_level("DEBUG").build(__name__)

# bots.py — quiet, with a console too
logger = lab().with_profile("conspiracy_theorist").with_level("WARNING").build(__name__)
```

Both modules share one rotating handler on `logs/app.log`. `loaders` writes its debug lines,
`bots` only its warnings, and every line carries the logger's name.

| Two loggers, same file…               | Result                                                              |
|---------------------------------------|---------------------------------------------------------------------|
| same experiment, same settings        | share one handler                                                   |
| same experiment, different settings   | share it with the **first** settings — `SharedFileSettingsWarning`  |
| different experiment (`FILE` vs `ROTATING`) | `LogFileClashError` — give one its own `with_file_args(filename=...)` |

The file closes when its last logger lets go. Handlers you attach yourself are never closed by
logger-lab.

### Thread safety

Every experiment and profile is thread-safe: log from any number of threads, and build or rebuild
loggers while others are logging — a logger switches to its new handlers in one step. (Several
*processes* writing one file is a different problem, still on the roadmap.)

---

## ⚡ Async logging

Add `async` and the calling thread only queues each record; one worker thread for the whole
process formats and writes it, in order, to the logger's outputs:

```python
from logger_lab import lab, drain

logger = lab().with_profile("investigator").with_experiment("ASYNC").build(__name__)
logger.info("never waits on the disk")

drain()   # optional: wait until everything queued is written (tests, before a crash report)
```

* Tracebacks survive the queue (`logger.exception(...)` still writes the traceback).
* The message is fixed when you log — changing an argument afterwards can't change the line.
* Queued records are written before the interpreter exits.
* `async` needs at least one output; on its own it raises `BuilderError`.

## 📡 Live subscribers

`with_subscriber(callback, level=None)` hands every record to your callback as it is logged — it
brings the `relay` experiment with it:

```python
import logging
from logger_lab import lab

alerts = []
logger = (
    lab()
    .with_experiment("standard")
    .with_subscriber(alerts.append, level="ERROR")   # only errors reach this one
    .build(__name__)
)
```

The callback gets the `logging.LogRecord` (treat it as read-only). A callback that raises is reported
like any handler error and never breaks logging. With `async`, callbacks run on the worker thread.

## 🖥️ GUI apps

The `gui` profile is `rotating_file` + `relay` + `async`: no console (windowed builds have no
stdout), and logging from the GUI thread never waits on the disk. Pass a Qt signal's `emit` as the
subscriber — Qt delivers it on the GUI thread:

```python
from PySide6.QtCore import QObject, Signal
from logger_lab import lab

class LogRelay(QObject):
    record_logged = Signal(object)

relay = LogRelay()
logger = (
    lab()
    .with_profile("gui")
    .with_subscriber(relay.record_logged.emit)
    .with_file_args(log_dir=user_log_dir)   # an installed app's working dir may not be writable
    .build("my_app")
)
```

Child loggers (`logging.getLogger("my_app.downloads")`) propagate into it, so every module's records
reach the file and the GUI.

---

## 🤖 AI Logging (Core Feature)

`logger-lab` includes a structured logging format designed for AI systems.

Logs become **machine-readable events**, not just text.

### Example Output

```json
{
  "timestamp": "2026-05-05T12:00:00+00:00",
  "level": "INFO",
  "logger": "app.auth",
  "message": "User logged in",
  "source": {
    "module": "auth",
    "function": "login",
    "line": 88
  },
  "extra": {
    "event": "user_login",
    "context": { "user_id": 42 },
    "tags": ["auth"]
  }
}
```

### Usage

Use `log_event()` — it constructs a fresh `extra` dict on every call so successive calls never share mutable state:

```python
from logger_lab import lab, log_event, ProfileType
import logging

logger = lab().with_profile(ProfileType.AGENT).build(__name__)

log_event(
    logger, logging.INFO, "User logged in",
    event="user_login",
    context={"user_id": 42},
    tags=["auth"],
)
```

---

When a record carries an exception (`logger.exception(...)`), the JSON gains an `"exception"`
object with `type`, `message` and the full `traceback`; `stack_info=True` adds a `"stack"` field.

---

## 🎚️ Levels

If you don't set a level, a logger logs at **INFO** — or **WARNING** when `minimalist` is part of
it (the `observer` profile). Set one with `with_level()`:

```python
lab().with_profile("investigator").build(__name__)                    # INFO
lab().with_profile("observer").build(__name__)                        # WARNING
lab().with_profile("investigator").with_level("DEBUG").build(__name__)
```

Level names are case-insensitive (custom ones from `logging.addLevelName` work too), and any
integer `0` or above is accepted. Anything else — a typo like `"DEBG"` — raises `InvalidLevelError`.

---

## 🚨 Error Handling

All exceptions inherit from `LabError` so you can catch broadly or precisely.

```
LabError
├── LabRegistryError
│   ├── ExperimentNotFoundError     — valid ExperimentType not registered
│   ├── ProfileNotFoundError        — valid ProfileType not registered
│   ├── TheoryNotFoundError         — theory is still a placeholder
│   ├── InvalidExperimentName       — unrecognized experiment string
│   ├── InvalidProfileName          — unrecognized profile string
│   └── InvalidTheoryName           — unrecognized theory string
├── LabConfigurationError
│   ├── InvalidLevelError           — unknown level name or invalid number
│   ├── HandlerConfigurationError   — handler failed to initialize
│   │   └── LogDirectoryError       — log directory mkdir/access failure
│   ├── ExperimentClashError        — two experiments on the same channel
│   ├── LogFileClashError           — file already open with a different experiment
│   ├── ExperimentRegistrationError — callable doesn't satisfy LabExperiment
│   └── ProfileRegistrationError    — bad profile callable or clashing composition
└── BuilderError                    — build() with nothing queued, or async with no output

Warnings (UserWarning, not errors):
DuplicateExperimentWarning — same experiment queued twice; the first is kept
SharedFileSettingsWarning  — a shared file keeps its first settings
```

### Broad catch

```python
from logger_lab import lab, LabError

try:
    logger = lab().with_profile("typo").build(__name__)
except LabError as exc:
    print(f"logger-lab error: {exc}")
```

### Precise catch

```python
from logger_lab import lab, InvalidProfileName, ExperimentClashError

try:
    logger = lab().with_profile("investigator").with_experiment("minimalist").build(__name__)
except InvalidProfileName as exc:
    print(f"Unknown profile: {exc}")   # lists valid names in the message
except ExperimentClashError as exc:
    print(f"Clashing experiments: {exc}")
```

---

## 🏗️ Architecture

```
logger_lab/
├── __init__.py           ← public API: lab(), log_event(), drain()
├── core/
│   ├── enums.py          ← ExperimentType, ProfileType, TheoryType, Channel
│   ├── registry.py       ← factories, channels, profile compositions — validated registration
│   └── builder.py        ← LabBuilder fluent interface (plan + build) + lab() factory
├── experiments/          ← atomic handler factories (level, **kwargs) → list[Handler]
│   ├── standard.py       ← RichHandler
│   ├── minimalist.py     ← StreamHandler, warnings only
│   ├── verbose.py        ← StreamHandler, full context
│   ├── file.py           ← FileHandler
│   ├── rotating_file.py  ← RotatingFileHandler
│   ├── ai.py             ← StreamHandler + JSONFormatter
│   ├── relay.py          ← RelayHandler, one per subscriber
│   └── asynchronous.py   ← async: the dispatcher
├── profiles/             ← prebuilt combinations, each declaring its *_EXPERIMENTS
│   ├── base.py           ← build_profile(): how every profile is built (yours too)
│   ├── observer.py
│   ├── investigator.py
│   ├── conspiracy_theorist.py
│   ├── ai_agent.py
│   └── gui.py
├── theories/             ← experiments still being researched
│   ├── _test_theory.py   ← harness: python -m logger_lab.theories._test_theory <THEORY>
│   ├── timed_file_exp.py ← TIMED_FILE (trial): daily / timed rotation
│   └── *_exp.py          ← one file per idea
└── logging_kernel/       ← shared infrastructure
    ├── constants.py      ← default file args
    ├── errors.py         ← full exception hierarchy + DuplicateExperimentWarning
    ├── formatters.py     ← JSONFormatter, log_event(), formatter factories
    ├── handlers.py       ← shared file table, atomic install/release, configure_handler(), get_log_dir()
    ├── dispatch.py       ← the async queue + worker thread, AsyncHandler, drain()
    └── normalizers.py    ← turns enum members and value strings into enums
(docs/ at the repository root: API reference, standards, trackers, roadmap)
```

---

## 🧬 Philosophy

`logger-lab` is built on three principles:

1. **Modularity** — Logging behavior should be reusable and composable.
2. **Clarity** — Logs should be easy to read and understand.
3. **Structure** — Logs should be usable as data, not just text.

> Logs are not just for debugging.
> They are inputs for analysis, automation, and intelligence.

---

## 🧪 Experimental Features

Some features live in the experimental zone (theories). Select one by enum or value string:

```python
from logger_lab import lab, TheoryType

# TIMED_FILE (trial): one file a day, keeping backup_count days
theory_logger = lab().with_theory(TheoryType.TIMED_FILE).build("doom")

# Theory-specific options go to that theory only; file args still come from with_file_args():
theory_logger = (
    lab()
    .with_theory("TIMED_FILE", when="midnight", interval=1, utc=False)
    .with_file_args(backup_count=7)
    .build("doom")
)
```

| Theory       | Stage       | What it does                                                         |
|--------------|-------------|----------------------------------------------------------------------|
| `TIMED_FILE` | trial       | Time-based rotation (`TimedRotatingFileHandler`), shared like `file` |
| others       | placeholder | `TRACE`, `PERFORMANCE`, `HTTP`, `SEC`, `DB` — raise `TheoryNotFoundError` |

These are unstable and may change.

---

## 🤝 Contributing

Contributions are welcome.

### Adding a new experiment

1. Create `logger_lab/theories/your_name_exp.py` with a module docstring describing the idea
2. Define `your_name_experiment(level: int = DEBUG, **kwargs) -> list[logging.Handler]`
3. Add the enum value to `TheoryType` in `core/enums.py`
4. Once it works, register it at the bottom of `core/registry.py`:
   `register_theory(TheoryType.YOUR_NAME, your_name_experiment, Channel.CONSOLE)`
5. Try it: `python -m logger_lab.theories._test_theory YOUR_NAME`
6. Add tests and document its purpose and behavior
7. After review, the Lab will promote it to an experiment

### Adding a new profile

Declare its experiments once and build it with `build_profile`; a profile combines at most one
experiment per channel:

```python
from logger_lab.profiles import build_profile
from logger_lab.experiments import verbose_experiment, file_experiment

MY_EXPERIMENTS = (verbose_experiment, file_experiment)

def my_profile(name, level=logging.INFO, **kwargs):
    return build_profile(name, level, *MY_EXPERIMENTS, **kwargs)
```

To make it selectable by name, register it (`register_profile`) — currently on a suggestion basis.

---

## 🧭 Roadmap

* [x] `async` and `relay` experiments, `gui` profile
* [ ] Promote `timed_file` (in trial)
* [ ] More experiments (`trace`, `performance`, `http`, `sec`, `db`)
* [ ] Process-safe logging (several processes, one file)
* [ ] Advanced profiles
* [ ] AI-assisted debugging tools
* [ ] Distributed tracing support
* [x] `py.typed` marker

---

## 🧑‍💻 Author

**Mosquito Lab (Cyber-Smoke)**
📧 [mosquitolab2024@protonmail.com](mailto:mosquitolab2024@protonmail.com)
🔗 [github.com/Mosquito-Lab/logger-lab](https://github.com/Mosquito-Lab/logger-lab)

---

## 📄 License

MIT LICENSE

---

## 🌱 Status

STABLE RELEASE: `v0.2.0`
* Still in active development. New experiments, profiles, and capabilities are being added continuously.
