# 🧪 logger-lab

> Logging, reimagined as a system.

`logger-lab` is a composable Python logging toolkit built around a simple idea:

**logging should be modular, readable, and adaptable, for both humans and machines.**

Instead of writing repetitive logging setup, you start from a **profile**, which is a common
composition. Or you compose your own logger from four kinds of building block: **outputs**,
**features**, **formats** and **catalysts**. Every logger it hands back is a plain
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

`lab()` is the one way to build a logger: say what you want, then `build(name)`.

### Summary of usage

```python
import logging
from logger_lab import lab, Feature

# A profile (a common composition):
profile_logger = lab().with_profile("conspiracy_theorist").build("profile_test")

# A profile, with features and options on top:
daily_logger = (
    lab()
    .with_profile("investigator")
    .with_output("file", filename="daily.log")         # configure the profile's file
    .with_feature(Feature.TIMED, at="02:00")              # daily at 02:00
    .with_level(logging.DEBUG)
    .build(__name__)
)

# Composed by hand:
hand_logger = lab().with_output("console").with_feature("MINIMAL").build("hand_test")
```

Every name can be given as its **enum member** or its **value string** (case-insensitive).

> A member's *name* can differ from its *value*. Use the value string:
> `ProfileType.AGENT` is `"AI_AGENT"`, `ProfileType.CONSPIRATOR` is `"CONSPIRACY_THEORIST"`.

---

## 🧱 The four kinds

Each kind has its own builder method.

| Kind         | Method                                  | Answers                     | Members                                |
|--------------|-----------------------------------------|-----------------------------|----------------------------------------|
| **Output**   | `with_output(name, **options)`          | where does feedback go?     | `console`, `file`, `relay`             |
| **Feature**  | `with_feature(name, on=None, **options)` | what extra does an output do? | `MINIMAL`, `VERBOSE`, `ROTATING`, `TIMED` |
| **Format**   | `with_format(name, on=None, **options)` | how does a record look?     | `RICH`, `TEXT`, `JSON`                 |
| **Catalyst** | `with_catalyst(name, **options)`        | how does every record flow? | `ASYNC`                                |

### 📤 Outputs

| Output    | Options (defaults)                                                  | Formats                        | Notes |
|-----------|---------------------------------------------------------------------|--------------------------------|-------|
| `console` | `stream="stderr"` (or `"stdout"`)                                   | `RICH` (default), `TEXT`, `JSON` | One console: Rich colors and tracebacks by default |
| `file`    | `log_dir="logs"`, `filename="app.log"`, `encoding="utf-8"`, `backup_count=3` | `TEXT` (default), `JSON` | Shared: one handler per file for the whole process |
| `relay`   | none                                                                | none                           | Every record to your callbacks; added by `with_subscriber()` |

### 🧩 Features

| Feature    | Fits           | Options (defaults)                         | What it does |
|------------|----------------|--------------------------------------------|--------------|
| `MINIMAL`  | console, file  | none                                       | Level and message only |
| `VERBOSE`  | console, file  | none                                       | Adds the logger name and `module.function:line` |
| `ROTATING` | file           | `max_bytes=5_242_880` (5 MiB)              | Roll over by size: `app.log.1` … `app.log.N` |
| `TIMED`    | file           | `every=1`, `unit="day"`, `day=None`, `at=None`, `utc=False` | Roll over on a schedule: `app.log.2026-10-22` |

Without a detail feature, a line carries **time, level and message** (plus the logger name in text).
`MINIMAL` and `VERBOSE` exclude each other on one output. They don't apply to `JSON`, because it
always carries every field.

### 🎨 Formats

| Format | Fits          | Looks like |
|--------|---------------|------------|
| `RICH` | console       | Rich colors, aligned columns, Rich tracebacks. The console's default |
| `TEXT` | console, file | Plain lines. The file's default |
| `JSON` | console, file | One JSON object per line (Mosquito Lab Logging Standard v1.2); on a file, JSON lines |

### ⚗️ Catalysts

| Catalyst | What it does |
|----------|--------------|
| `ASYNC`  | The calling thread only queues; one worker thread formats and writes ([below](#-async-logging)) |

---

## 🧫 Profiles

Profiles are **the common compositions**, written as builder calls. Start from one, then add or
configure on top. It is almost always simpler than composing by hand.

| Profile               | Value                   | Composition                            | Use case                             |
|-----------------------|-------------------------|----------------------------------------|--------------------------------------|
| `observer`            | `"OBSERVER"`            | console + `MINIMAL`                    | Low noise: level and message only    |
| `investigator`        | `"INVESTIGATOR"`        | console + file                         | Development: Rich console + disk     |
| `conspiracy_theorist` | `"CONSPIRACY_THEORIST"` | console + file + `VERBOSE` + `ROTATING` | Deep archival: nothing missed       |
| `ai_agent`            | `"AI_AGENT"`            | console + `JSON`                       | Structured JSON for pipelines        |
| `gui`                 | `"GUI"`                 | file + `ROTATING` + relay + `ASYNC`    | Desktop apps: no console, and nothing blocks the GUI thread |

```python
from logger_lab import lab, ProfileType

payload = "super dangerous and malicious payload!"

logger = lab().with_profile(ProfileType.CONSPIRATOR).with_level("DEBUG").build(__name__)
logger.debug("Payload received: %s", payload)

try:
    raise ValueError("unexpected response")
except ValueError:
    logger.exception("Request failed")   # the traceback reaches the console and the file
```

One profile per logger: a second `with_profile()` raises `CompositionError`.

---

## 🧬 Composition

### Options live on the building blocks

`with_output()` **adds** an output. If the logger already has it (from a profile, say), it
**configures** it instead. The same goes for features and catalysts: calling again merges
the options, and later values win.

```python
from logger_lab import lab

logger = (
    lab()
    .with_profile("conspiracy_theorist")
    .with_output("file", log_dir="run_logs", filename="session.log", backup_count=5)
    .with_feature("ROTATING", max_bytes=1_048_576)
    .build(__name__)
)
```

An option a building block doesn't declare is a `CompositionError` that lists the valid ones.
A typo never goes unnoticed.

### `on=`: which output

A feature or format goes on **every queued output it fits**. `on=` narrows it to one:

```python
logger = (
    lab()
    .with_profile("investigator")
    .with_feature("MINIMAL", on="console")   # a quiet terminal…
    .with_format("JSON", on="file")          # …and JSON lines on disk
    .build(__name__)
)
```

### Rotation: by size, on a schedule, or both

```python
lab().with_profile("investigator").with_feature("ROTATING", max_bytes=10_485_760)
lab().with_profile("investigator").with_feature("TIMED", at="02:00")                    # daily at 02:00
lab().with_profile("investigator").with_feature("TIMED", every=6, unit="hours")          # 00:00, 06:00, 12:00, 18:00
lab().with_profile("investigator").with_feature("TIMED", unit="hour", at=":30")          # every hour at half past
lab().with_profile("investigator").with_feature("TIMED", day="friday", at="18:00")       # weekly, on Fridays
lab().with_profile("investigator").with_feature("TIMED", every=2, unit="weeks", day="monday")
lab().with_profile("investigator").with_feature("TIMED", every=3, unit="months")         # quarterly
lab().with_profile("investigator").with_feature("TIMED", unit="week").with_feature("ROTATING")
```

The `TIMED` options follow the popular [`schedule`](https://schedule.readthedocs.io/) package, as
keyword arguments. `every=6, unit="hours"` is `schedule.every(6).hours`.

* `every=`: how many units make a period, 1 or more. It defaults to 1, so a unit on its own
  means one of that unit: `unit="hour"` rolls over every hour.
* `unit=`: `"minute"`, `"hour"`, `"day"` (default), `"week"` or `"month"`. Plurals work too.
* `day=`: `"monday"` … `"sunday"`. It makes the schedule weekly, so `unit` can be left out.
* `at=`: when a period starts. Use `":MM"` for an hour, and `"HH:MM"` for a day, week or month.
* `utc=True`: boundaries and backup names in UTC instead of local time. That is the same moment
  on every machine, with no double or missing hour when the clocks change.
* `backup_count` (a file option) is how many backups are kept. The oldest go first.

`unit=` and `day=` also take the `Unit` and `Day` enums, so your editor can catch a typo
before the logger does:

```python
from logger_lab import Day, Unit, lab

lab().with_profile("investigator").with_feature("TIMED", every=6, unit=Unit.HOUR)
lab().with_profile("investigator").with_feature("TIMED", day=Day.FRIDAY, at="18:00")
```

Unlike `schedule`, periods are anchored to the calendar, not to when the app started. So a
restart never moves the schedule, and `every=3, unit="months"` gives quarters. There is also a
`month` unit, which `schedule` doesn't have.

| Rotation        | Backup names                                          |
|-----------------|-------------------------------------------------------|
| `ROTATING`      | `app.log.1` (newest) … `app.log.N`                    |
| `TIMED`         | `app.log.2026-10-22` (`.2026-10` monthly, `.2026-10-22_14` hourly) |
| both            | `app.log.2026-10-22.1`, `app.log.2026-10-22.2` …      |

A backup is never overwritten: if a name is taken (say, the app restarted mid-day), a counter is
added. Monthly rotation is something the stdlib's timed handler can't do.

### Composition rules

Building blocks are made to work together, and the builder refuses compositions that can't:

* **Features never bring an output.** `ROTATING` on a logger with no file is an error that says
  how to add one. It never adds a silent extra file.
* **One detail feature and one format per output**, and only where they work: `ROTATING` on the
  console, `RICH` on a file or `MINIMAL` on `JSON` all raise `CompositionError`.
* **One profile per logger, one catalyst per group** (one dispatcher).

```python
lab().with_profile("observer").with_feature("ROTATING").build(__name__)
# CompositionError: 'ROTATING' needs a file output: add .with_output('file'),
# or start from a profile such as 'investigator'
```

Composing by hand what a profile already says works, but warns with `ProfileSuggestionWarning`:

```python
lab().with_output("console").with_output("file").build(__name__)
# ProfileSuggestionWarning: console + file is the 'INVESTIGATOR' profile: use
# .with_profile('investigator'), then add features or options on top
```

Check a composition without building anything with `plan()`:

```python
lab().with_profile("investigator").with_format("JSON", on="file").plan().names()
# {'CONSOLE': {'format': 'RICH', 'features': []},
#  'FILE': {'format': 'JSON', 'features': []}, 'catalysts': []}
```

### Many modules, one file

Give every module its own logger (`__name__`), and let each pick its own composition and level.
They can all write to the same `logs/app.log`. Each log file is opened **once per process**: every
logger writing to it shares one handler, so records never collide and rotation keeps working.

```python
# loaders.py: chatty, file only
logger = (
    lab().with_output("file").with_feature("VERBOSE").with_feature("ROTATING")
    .with_level("DEBUG").build(__name__)
)

# bots.py: quiet, with a console too
logger = lab().with_profile("conspiracy_theorist").with_level("WARNING").build(__name__)
```

Both modules share one rotating handler on `logs/app.log`. `loaders` writes its debug lines,
`bots` only its warnings, and every line carries the logger's name.

| Two loggers, same file…                    | Result                                                              |
|--------------------------------------------|---------------------------------------------------------------------|
| same format and rotation, same settings    | share one handler                                                   |
| same format and rotation, other settings   | share it with the **first** settings, plus `SharedFileSettingsWarning` |
| different format or rotation               | `LogFileClashError`. Give one its own `with_output("file", filename=...)` |

The file closes when its last logger lets go. Handlers you attach yourself are never closed by
logger-lab.

### Thread safety

Every output, feature and profile is thread-safe: log from any number of threads, and build or
rebuild loggers while others are logging. A logger switches to its new handlers in one step.
(Several *processes* writing one file is a different problem, still on the roadmap.)

---

## ⚡ Async logging

> How async, subscribers and Qt fit together, with the guarantees and limits: the
> [Feedback Guide](https://github.com/Mosquito-Lab/logger-lab/blob/main/docs/Feedback_Guide.md).

Add the `ASYNC` catalyst and the calling thread only queues each record; one worker thread for the
whole process formats and writes it, in order, to the logger's outputs:

```python
from logger_lab import lab, drain

logger = lab().with_profile("investigator").with_catalyst("ASYNC").build(__name__)
logger.info("never waits on the disk")

drain()   # optional: wait until everything queued is written (tests, before a crash report)
```

* Tracebacks survive the queue (`logger.exception(...)` still writes the traceback).
* The message is fixed when you log. Changing an argument afterwards can't change the line.
* Queued records are written before the interpreter exits. A stuck subscriber can delay the exit by
  5 seconds at most (`DRAIN_TIMEOUT`); whatever is still queued then is lost.
* `ASYNC` needs at least one output; on its own it raises `CompositionError`.

## 📡 Live subscribers

`with_subscriber(callback, level=None)` hands every record to your callback as it is logged. It
brings the `relay` output with it:

```python
from logger_lab import lab

alerts = []
logger = (
    lab()
    .with_output("console")
    .with_subscriber(alerts.append, level="ERROR")   # only errors reach this one
    .build(__name__)
)
```

The callback gets the `logging.LogRecord` (treat it as read-only). A callback that raises is
reported like any handler error and never breaks logging. With `ASYNC`, callbacks run on the
worker thread. A record logged *inside* a callback still reaches files and consoles, but it is
never relayed to subscribers again, so a subscriber that logs can't feed itself.

## 🖥️ GUI apps

The `gui` profile is file + `ROTATING` + relay + `ASYNC`: no console (windowed builds have no
stdout or stderr), and logging from the GUI thread never waits on the disk. Pass a Qt signal's
`emit` as the subscriber, and Qt delivers it on the GUI thread:

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
    .with_output("file", log_dir=user_log_dir)   # an installed app's working dir may not be writable
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
  "timestamp": "2026-05-05 12:00:00",
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

Use `log_event()`. It builds a fresh `extra` dict on every call, so successive calls never
share mutable state:

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

The `JSON` format works on a file too. `with_format("JSON", on="file")` writes JSON lines, ready
for `jq`, a log aggregator or an LLM.

When a record carries an exception (`logger.exception(...)`), the JSON gains an `"exception"`
object with `type`, `message` and the full `traceback`. `stack_info=True` adds a `"stack"` field.

---

## 🎚️ Levels

Every logger logs at **INFO** unless you set a level. That is one default, for every profile.
Change it intentionally with `with_level()`:

```python
lab().with_profile("investigator").build(__name__)                    # INFO
lab().with_profile("observer").with_level("WARNING").build(__name__)  # quieter
lab().with_profile("investigator").with_level("DEBUG").build(__name__)
```

Level names are case-insensitive (custom ones from `logging.addLevelName` work too), and any
integer `0` or above is accepted. Anything else raises `InvalidLevelError`, such as a typo
like `"DEBG"`.

---

## 🚨 Error Handling

All exceptions inherit from `LabError` so you can catch broadly or precisely.

```
LabError
├── LabRegistryError
│   ├── InvalidNameError            unrecognized name of any kind (lists the valid ones)
│   ├── TheoryNotFoundError         theory is still a placeholder
│   └── RegistrationError           a theory spec that doesn't hold up, or a lookup that finds nothing
├── LabConfigurationError
│   ├── InvalidLevelError           unknown level name or invalid number
│   ├── CompositionError            a composition that can't work (says how to fix it)
│   ├── HandlerConfigurationError   handler failed to initialize
│   │   └── LogDirectoryError       log directory mkdir/access failure
│   └── LogFileClashError           file already open with a different format or rotation
└── BuilderError                    nothing queued, or ASYNC with nothing built to wrap

Warnings (UserWarning, not errors):
ProfileSuggestionWarning   a hand-made composition that a profile already provides
SharedFileSettingsWarning  a shared file keeps its first settings
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
from logger_lab import lab, InvalidNameError, CompositionError

try:
    logger = lab().with_profile("observer").with_feature("VERBOSE").build(__name__)
except InvalidNameError as exc:
    print(f"Unknown {exc.kind}: {exc}")   # lists valid names in the message
except CompositionError as exc:
    print(f"Can't compose that: {exc}")   # MINIMAL and VERBOSE both set the detail
```

---

## 🏗️ Architecture

```
logger_lab/
├── __init__.py           ← public API: lab(), log_event(), drain(), names, errors, __version__
├── core/
│   ├── enums.py          ← Kind, Output, Feature, Format, Catalyst, Unit, Day, ProfileType, TheoryType, value_of()
│   ├── specs.py          ← OutputSpec, FeatureSpec, FormatSpec, CatalystSpec, ProfileSpec, OutputPlan
│   ├── registry.py       ← the tables of every spec; register_theory() checks a theory
│   └── builder.py        ← LabBuilder (with_* → plan → build) + lab()
├── outputs/              ← where feedback goes
│   ├── console.py        ← LabRichHandler (RICH) or StreamHandler (TEXT / JSON)
│   ├── file.py           ← the shared LabFileHandler
│   └── relay.py          ← RelayHandler, one per subscriber
├── features/             ← extra behavior on an output
│   ├── detail.py         ← MINIMAL, VERBOSE
│   └── rotation.py       ← ROTATING, TIMED
├── formats/              ← RICH, TEXT, JSON
├── catalysts/            ← how every record flows
│   └── asynchronous.py   ← ASYNC
├── profiles/             ← the common compositions, one recipe each
│   ├── observer.py
│   ├── investigator.py
│   ├── conspiracy_theorist.py
│   ├── ai_agent.py
│   └── gui.py
├── theories/             ← building blocks still being researched
│   └── *_exp.py          ← one file per idea, with its likely kind
└── logging_kernel/       ← shared infrastructure
    ├── constants.py      ← default options
    ├── errors.py         ← full exception hierarchy + warnings
    ├── formatters.py     ← JSONFormatter, text layouts, log_event()
    ├── handlers.py       ← LabFileHandler, shared file table, atomic install/release, get_log_dir()
    ├── rollover.py       ← SizeRule, TimeRule: the rotation arithmetic
    ├── dispatch.py       ← the async queue + worker thread, AsyncHandler, drain()
    └── normalizers.py    ← turns enum members and value strings into enums
(docs/ at the repository root: API reference, standards, trackers, roadmap)
```

---

## 🧬 Philosophy

`logger-lab` is built on three principles:

1. **Modularity**: logging behavior should be reusable and composable.
2. **Clarity**: logs should be easy to read and understand.
3. **Structure**: logs should be usable as data, not just text.

> Logs are not just for debugging.
> They are inputs for analysis, automation, and intelligence.

---

## 🧪 Experimental Features

Some building blocks live in the experimental zone (theories). A theory can be any of the four
kinds, and acts as that kind once it reaches trial. A few ideas are helpers instead (`LIFECYCLE`,
`PERFORMANCE`, `DB`), which will join the API beside `log_event`:

```python
from logger_lab import lab, TheoryType

logger = lab().with_profile("gui").with_theory(TheoryType.THROTTLE).build("doom")   # once THROTTLE is in trial
```

| Theory | Stage       | What it does |
|--------|-------------|--------------|
| all    | placeholder | In roadmap order: `TRACE`, `LIFECYCLE`, `THROTTLE`, `PERFORMANCE`, `PROCESS`, `HTTP`, `SEC`, `DB`; they raise `TheoryNotFoundError` |

These are unstable and may change.

---

## 🤝 Contributing

Contributions are welcome.

### Adding a new building block

1. Create `logger_lab/theories/your_name_exp.py` with a module docstring describing the idea
   and its likely kind
2. Add the enum value to `TheoryType` in `core/enums.py`
3. Write its spec: an `OutputSpec`, `FeatureSpec`, `FormatSpec` or `CatalystSpec`, with
   `TheoryType.YOUR_NAME` as its member
4. Once it works, register it: `register_theory(Kind.FEATURE, YOUR_NAME_SPEC)`.
   The spec is checked as it comes in.
5. Try it in a test: `lab().with_profile("investigator").with_theory("YOUR_NAME")`
6. Add tests and document its purpose and behavior
7. After review, the Lab will promote it to a building block of its kind

### Adding a new profile

A profile is a recipe of builder calls, so it obeys every composition rule:

```python
from logger_lab.core.enums import Feature, Output, ProfileType
from logger_lab.core.specs import ProfileSpec

def night_watch(builder):
    return builder.with_output(Output.FILE).with_feature(Feature.TIMED, at="02:00")

NIGHT_WATCH_SPEC = ProfileSpec(member=ProfileType.NIGHT_WATCH, recipe=night_watch, summary="file + TIMED")
```

Add its `ProfileType` member, and its spec to `PROFILE_SPECS` in `profiles/__init__.py`. That is
currently on a suggestion basis. The test suite plans every profile, so one that can't compose
fails there.

---

## 🧭 Roadmap

* [x] `ASYNC` and `relay`, `gui` profile
* [x] Four kinds of building block; `TIMED` promoted to a feature (size + time together)
* [x] `py.typed` marker
* [ ] Publish 0.2.0
* [ ] The feedback layer: `TRACE` (correlation IDs) with `LIFECYCLE` (started, progress, done and
  failed events), then `THROTTLE` (rate limits for subscribers)
* [ ] `PERFORMANCE` (timing, as lifecycle events), then process-safe logging (`PROCESS`)
* [ ] Specialized: `HTTP`, `SEC`, `DB`
* [ ] Then: configuration from env or a dict, and an exception helper

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

Current version: `0.2.0`.

Still in active development: new building blocks, profiles and capabilities are being added.
