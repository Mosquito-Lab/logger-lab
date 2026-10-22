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
from logger_lab import get_logger

logger = get_logger(__name__, profile="INVESTIGATOR")

logger.info("System online")
logger.debug("Inspecting state")
logger.error("Something broke")
```

### Summary of usage
Every experiment, profile and theory can be picked by its **enum member** or its **value string**
(case-insensitive) — in `get_logger()` and in `lab()` alike:

```python
import logging
from logger_lab import lab, get_logger, ExperimentType

# Profiles (prebuilt combinations):
profile_logger = get_logger(name="profile_test", profile="conspiracy_theorist")

# Experiments (single handler factories):
experiment_logger = get_logger(name="experiment_test", experiment=ExperimentType.MINIMALIST)

# Fluent builder (custom composition) — its own file, because profile_logger's
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
| `ai`            | `"AI"`         | json    | `StreamHandler` (stderr) | Structured JSON — Mosquito Lab Standard v1        |

### Using a single experiment

```python
from logger_lab import get_logger

logger = get_logger(__name__, experiment="minimalist")
logger.info("Ready")
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

```python
from logger_lab import get_logger, ProfileType

payload = "super dangerous and malicious payload!"

logger = get_logger(__name__, profile=ProfileType.CONSPIRATOR)
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

Calling it again replaces every arg — omitted ones go back to their defaults. `get_logger()` has no
file args; use `lab()` when you need them.

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
*processes* writing one file is a different problem — see the `ASYNC` theory on the roadmap.)

---

## 🤖 AI Logging (Core Feature)

`logger-lab` includes a structured logging format designed for AI systems.

Logs become **machine-readable events**, not just text.

### Example Output

```json
{
  "timestamp": "2026-05-05T12:00:00+00:00",
  "level": "INFO",
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
from logger_lab import get_logger, log_event, ProfileType
import logging

logger = get_logger(__name__, profile=ProfileType.AGENT)

log_event(
    logger, logging.INFO, "User logged in",
    event="user_login",
    context={"user_id": 42},
    tags=["auth"],
)
```

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
│   ├── InvalidLevelError           — bad level string or int
│   ├── HandlerConfigurationError   — handler failed to initialize
│   │   └── LogDirectoryError       — log directory mkdir/access failure
│   ├── ExperimentClashError        — two experiments on the same channel
│   ├── LogFileClashError           — file already open with a different experiment
│   ├── ExperimentRegistrationError — callable doesn't satisfy LabExperiment
│   └── ProfileRegistrationError    — bad profile callable or clashing composition
└── BuilderError                    — build() called with nothing queued

Warnings (UserWarning, not errors):
DuplicateExperimentWarning — same experiment queued twice; the first is kept
SharedFileSettingsWarning  — a shared file keeps its first settings
```

### Broad catch

```python
from logger_lab import get_logger, LabError

try:
    logger = get_logger(__name__, profile="typo")
except LabError as exc:
    print(f"logger-lab error: {exc}")
```

### Precise catch

```python
from logger_lab import get_logger, InvalidProfileName, ExperimentClashError

try:
    logger = get_logger(__name__, profile="investigator", experiment="minimalist")
except InvalidProfileName as exc:
    print(f"Unknown profile: {exc}")   # lists valid names in the message
except ExperimentClashError as exc:
    print(f"Clashing experiments: {exc}")
```

---

## 🏗️ Architecture

```
logger_lab/
├── __init__.py           ← public API: get_logger(), lab(), log_event()
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
│   └── ai.py             ← StreamHandler + JSONFormatter
├── profiles/             ← prebuilt combinations, each declaring its *_EXPERIMENTS
│   ├── _base.py          ← _build_profile() shared skeleton
│   ├── observer.py
│   ├── investigator.py
│   ├── conspiracy_theorist.py
│   └── ai_agent.py
├── theories/             ← experiments still being researched
│   ├── _test_theory.py   ← harness: python -m logger_lab.theories._test_theory <THEORY>
│   └── *_exp.py          ← one file per theory
├── logging_kernel/       ← shared infrastructure
│   ├── constants.py      ← default file args
│   ├── errors.py         ← full exception hierarchy + DuplicateExperimentWarning
│   ├── formatters.py     ← JSONFormatter, log_event(), formatter factories
│   ├── handlers.py       ← shared file table, atomic install/release, configure_handler(), get_log_dir()
│   └── normalizers.py    ← turns enum members and value strings into enums
└── docs/                 ← API reference, standards, trackers, roadmap
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
from logger_lab import get_logger, lab, TheoryType

theory_logger = get_logger(name="doom", theory=TheoryType.TIMED_FILE)

# Theory-specific options go to that theory only:
theory_logger = lab().with_theory("TIMED_FILE", when="midnight").build("doom")
```

No theory has left the placeholder stage yet, so selecting one raises `TheoryNotFoundError` for now.
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

Currently just on a suggestion basis. A profile combines at most one experiment per channel.

---

## 🧭 Roadmap

* [ ] More experiments (`timed_file`, `trace`, `async`, `performance`, `http`, `sec`, `db`)
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
