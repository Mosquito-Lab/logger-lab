# logger-lab API Reference

## Scope and import policy

logger-lab is a composable layer over the standard-library `logging` module.
It never replaces `logging.Logger`: every entry point returns a plain stdlib
logger with handlers attached, so anything that works with `logging` keeps
working.

The top-level `logger_lab` package is the consumer-facing surface. Lower-level
building blocks are imported from their subpackages.

```python
from logger_lab import lab, log_event, drain, ExperimentType, ProfileType, TheoryType, LabError
from logger_lab.core import EXPERIMENTS, PROFILES, Channel, register_theory
from logger_lab.logging_kernel import configure_handler, get_log_dir, JSONFormatter
```

Names prefixed with `_` are not public API (`registry._validate_*`, the `_test_theory` harness).

## The composition model

logger-lab has three building blocks, and the builder composes them.

| Block | What it is | Shape | Where it lives |
| --- | --- | --- | --- |
| **Experiment** | One logging behavior: one handler, one format, one **channel** | `(level: int, **kwargs) -> list[Handler]` | `logger_lab/experiments/` |
| **Dispatcher** | A special experiment (`async`) that wraps a logger's other handlers instead of adding one | `@dispatcher (level, *, handlers, **kwargs) -> list[Handler]` | `logger_lab/experiments/asynchronous.py` |
| **Profile** | A named combination of experiments, declared as a tuple | `(name: str, level: int, **kwargs) -> Logger` plus `*_EXPERIMENTS` | `logger_lab/profiles/` |
| **Theory** | An experiment still being researched | Same as an experiment | `logger_lab/theories/` |

### Channels

Every experiment and theory is registered on one `Channel`. **A logger holds at
most one experiment per channel**, so handlers never compete for the same
output.

| `Channel` | Experiments |
| --- | --- |
| `CONSOLE` | `standard`, `verbose`, `minimalist` |
| `FILE` | `file`, `rotating_file`, `TIMED_FILE` (theory) |
| `JSON` | `ai` |
| `LIVE` | `relay` (records to your subscribers) |
| `DISPATCH` | `async`: not an output; how records reach the others |

### How the builder composes

```text
lab() ──► with_profile(...)        ┐
      ──► with_experiment(...)     │  recorded only, nothing built
      ──► with_theory(..., **opts) │
      ──► with_level(...)          │
      ──► with_file_args(...)      │
      ──► with_subscriber(cb, lvl) ┘
      ──► plan()   1. profile → its declared experiments, then everything queued, in order
                   2. subscribers but no relay planned → relay added
                   3. same entry again  → DuplicateExperimentWarning, first one kept
                   4. two entries, one channel → ExperimentClashError (names both + origin)
      ──► build(name)
                   1. plan()  (fails before anything is touched)
                   2. each planned output factory(level, **file_args [+ theory options],
                      logger_name=name, subscribers=...) → file experiments get their handler
                      from the shared file table
                   3. a dispatcher (async), if planned, wraps those outputs → one AsyncHandler
                   4. install_handlers(): one atomic swap onto getLogger(name), then the old
                      handlers are released (closed only when last, and only if logger-lab made them)
                   5. logger.setLevel(level); logger.propagate = False
```

### Across loggers: one file, one handler

The channel rule is per logger. Across loggers, every log file has exactly one
handler in the process (`share_file_handler()`), so each module can pick its own
experiments and level and still write to one `app.log`.

| A second logger asks for an open file with… | Result |
| --- | --- |
| the same experiment and settings | shares the handler |
| the same experiment, different settings (`max_bytes`, `encoding`, …) | shares it with the **first** settings + `SharedFileSettingsWarning` |
| a different experiment (`FILE` vs `ROTATING`) | `LogFileClashError` (use another `filename`) |
| …and it's the file's only logger, being rebuilt | a new handler replaces the old one |

Shared file handlers have no level of their own (`NOTSET`). Each logger's level
filters its own records. The file closes when its last logger releases it.

### Thread safety

Every experiment and profile is thread-safe within one process:
- **Writes:** handlers lock each write, and formatters hold no state.
- **Files:** one handler per file, created under a lock.
- **Building:** `build()` swaps a logger's handlers in one assignment, so a
  thread that's logging finishes its record on the old list. Released file
  handlers stay closed (`StayClosedMixin`) and never reopen.
- **Async:** one queue and **one worker thread for the whole process**, however
  many loggers use `async`. Records keep their order; a record's message is fixed
  on the calling thread; queued records are written before exit (`stop_worker`
  runs at exit, before `logging.shutdown`).
- **Builders:** a single `LabBuilder` instance is not meant to be shared
  between threads while it is being configured.
- **Processes:** several processes writing one file is not covered.

### Async dispatch

| | Without `async` | With `async` |
| --- | --- | --- |
| Who formats and writes | the thread that logged | the `logger-lab-dispatch` worker |
| Caller cost per written file record (measured, Windows) | ~27 µs | ~14 µs, and never waits on a slow disk |
| Tracebacks (`logger.exception`) | written | written (unlike the stdlib `QueueHandler`) |
| A subscriber runs on | the thread that logged | the worker |
| Wait for everything queued | — | `drain(timeout=None)`, from `logger_lab` |

`drain()` called from the worker itself (say, inside a subscriber) returns `False`
at once instead of waiting on itself. Releasing an async logger waits for its
queued records, then releases its outputs.

`build()` never calls the profile function. It builds the profile's declared
experiments itself, which is what lets it check them against everything else.
The profile function stays available for direct calls (`investigator(__name__)`).

**Kwargs contract.** The builder forwards the *same* file args to every
factory. File experiments take the ones they understand; console experiments
must still accept `**kwargs` and ignore them.

## Entry points

| API | Import | Purpose |
| --- | --- | --- |
| `lab()` | `logger_lab` | Returns a fresh `LabBuilder`. **The one way to build a logger** — there is no separate one-call shortcut. |
| `log_event(logger, level, msg, *, event, context=None, tags=None)` | `logger_lab` | Emits one structured record (`event`, `context`, `tags` in `extra`). Pairs with the `ai` experiment and the `ai_agent` profile. |

```python
import logging
from logger_lab import lab, ExperimentType

logger = lab().with_profile("investigator").build(__name__)

logger = (
    lab()
    .with_profile("investigator")
    .with_experiment(ExperimentType.AI)
    .with_level("INFO")
    .with_file_args("run_logs", filename="session.log")
    .build(__name__)
)
```

## Names: member or value

Everything is selectable by its enum **member** or its **value string**,
case-insensitively, in every entry point. The member *name* as a string is not
an alias.

| Member | Value string | ✔ accepted | ✘ rejected |
| --- | --- | --- | --- |
| `ExperimentType.ROTATING_FILE` | `"ROTATING"` | `ExperimentType.ROTATING_FILE`, `"ROTATING"`, `"rotating"` | `"ROTATING_FILE"`, `"rotating_file"` |
| `ProfileType.AGENT` | `"AI_AGENT"` | `ProfileType.AGENT`, `"AI_AGENT"`, `"ai_agent"` | `"AGENT"` |
| `ProfileType.CONSPIRATOR` | `"CONSPIRACY_THEORIST"` | `ProfileType.CONSPIRATOR`, `"conspiracy_theorist"` | `"CONSPIRATOR"` |
| every other member | same as its name | member, value, lowercase value | — |

## `LabBuilder`

Every `with_*` method only records state and returns `self`. Nothing is built
and no files are opened until `build()`.

| Method | Purpose |
| --- | --- |
| `with_experiment(experiment)` | Queues an `ExperimentType` member or value string. You can queue several; they are applied in order, after the profile's. Theories are not accepted here. |
| `with_theory(theory, **options)` | Queues a `TheoryType` member or value string. *options* go to that theory's factory only, on top of the file args (for example `when="midnight"`). Queuing the same theory again replaces its options. |
| `with_profile(profile)` | Sets the profile (`ProfileType` or value string). Only one is allowed, and a second call replaces the first. Its experiments come first in the plan. |
| `with_level(level)` | Sets the level on the logger and every handler. Takes level names (case-insensitive, custom ones too) or integers `0` or above; anything else raises `InvalidLevelError`. If never called: **INFO**, or **WARNING** when `minimalist` is in the logger (`default_level`). |
| `with_file_args(log_dir='logs', filename='app.log', encoding='utf-8', max_bytes=5 MiB, backup_count=3)` | Sets where and how file experiments write. The args are forwarded to every experiment built, the profile's included. A second call replaces **all** of them. |
| `with_subscriber(callback, level=None)` | Adds a subscriber: *callback* gets every record that passes *level* (`None` → the logger's level). Brings the `relay` experiment with it. Each call adds another. The record is shared; treat it as read-only. |
| `plan()` | Returns the de-duplicated, clash-free build order without building anything. Warns on duplicates, raises `ExperimentClashError` on clashes and `TheoryNotFoundError` on placeholders. |
| `build(name)` | Plans, then builds the logger (see the composition model above). Returns a stdlib `Logger` with `propagate = False`. |

### File args: which experiment uses what

| Arg | `file` | `rotating_file` | `TIMED_FILE` | everything else |
| --- | --- | --- | --- | --- |
| `log_dir` | ✔ | ✔ | ✔ | ignored |
| `filename` | ✔ | ✔ | ✔ | ignored |
| `encoding` | ✔ | ✔ | ✔ | ignored |
| `max_bytes` | ignored | ✔ | ignored | ignored |
| `backup_count` | ignored | ✔ | ✔ (days, with `"midnight"`) | ignored |

`log_dir` is created, parents included, by `get_log_dir()` when the handler is
built.

## Experiments

| `ExperimentType` | Value | Channel | Factory | Handler | Output |
| --- | --- | --- | --- | --- | --- |
| `STANDARD` | `"STANDARD"` | console | `standard_experiment` | `rich.logging.RichHandler` | Colored console output with Rich tracebacks |
| `VERBOSE` | `"VERBOSE"` | console | `verbose_experiment` | `StreamHandler` | `time \| name \| level \| module.func:line \| message` |
| `MINIMALIST` | `"MINIMALIST"` | console | `minimalist_experiment` | `StreamHandler` | `LEVEL: message`. The factory defaults to `WARNING` |
| `FILE` | `"FILE"` | file | `file_experiment` | `SharedFileHandler` (a `FileHandler`) | Plain-text file at `log_dir/filename`, shared across loggers |
| `ROTATING_FILE` | `"ROTATING"` | file | `rotating_file_experiment` | `SharedRotatingFileHandler` (a `RotatingFileHandler`) | Size-rotated file (`app.log`, `app.log.1`, …), shared across loggers |
| `AI` | `"AI"` | json | `ai_experiment` | `StreamHandler` (stderr) + `JSONFormatter` | One JSON object per line, Mosquito Lab Logging Standard v1.1 |
| `RELAY` | `"RELAY"` | live | `relay_experiment` | `RelayHandler`, one per subscriber | Each record to its subscriber's callback; a callback that raises is reported, never propagated |
| `ASYNC` | `"ASYNC"` | dispatch | `async_experiment` | `AsyncHandler` (wraps the others) | Nothing itself: the logger's outputs are written on the dispatch worker thread. Needs at least one output |

Factories can also be called directly and their handlers attached to any
logger:

```python
from logger_lab.experiments import rotating_file_experiment

for handler in rotating_file_experiment(logging.DEBUG, log_dir="logs", max_bytes=1_048_576):
    my_logger.addHandler(handler)
```

## Profiles

| `ProfileType` | Value | Declared experiments | Use case |
| --- | --- | --- | --- |
| `OBSERVER` | `"OBSERVER"` | `OBSERVER_EXPERIMENTS` = `minimalist` | Production, warnings and above. The factory defaults to `WARNING` |
| `INVESTIGATOR` | `"INVESTIGATOR"` | `INVESTIGATOR_EXPERIMENTS` = `standard` + `file` | Everyday development |
| `CONSPIRATOR` | `"CONSPIRACY_THEORIST"` | `CONSPIRACY_THEORIST_EXPERIMENTS` = `verbose` + `rotating_file` | Capture everything, rotated |
| `AGENT` | `"AI_AGENT"` | `AI_AGENT_EXPERIMENTS` = `ai` | Structured JSON for pipelines and LLMs |
| `GUI` | `"GUI"` | `GUI_EXPERIMENTS` = `rotating_file` + `relay` + `async` | Desktop apps (LabFrame): no console, file and subscribers off the calling thread |

Each profile module declares its experiments once as a tuple of factories, and
the profile function is `build_profile(name, level, *THAT_TUPLE, **kwargs)` (public, in `logger_lab.profiles`, for custom profiles too).
The registry reads the same tuple, so a profile is defined in exactly one place.

**Level defaults (one rule everywhere).** No level set → **INFO**, or **WARNING**
when `minimalist` is part of the logger (so `observer`). That holds through
`lab()` and direct profile calls alike; `with_level()` /
`level=` always wins.

## Theories

| Stage | What exists | Registered? | Selecting it |
| --- | --- | --- | --- |
| Idea | `theories/name_exp.py` with the plan in its docstring | No | — |
| Placeholder | Plus a `TheoryType` value | No | `TheoryNotFoundError` |
| Trial | A working factory, registered with `register_theory()` | Yes | Builds like an experiment |
| Promoted | Moved to `experiments/` with an `ExperimentType` value | As an experiment | — |

| `TheoryType` | Stage | Channel | Options (`with_theory(..., **options)`) |
| --- | --- | --- | --- |
| `TIMED_FILE` | **trial** | FILE | `when="midnight"`, `interval=1`, `utc=False`, `at_time=None`; plus file args `log_dir`/`filename`/`encoding`/`backup_count` |
| `TRACE`, `PERFORMANCE`, `HTTP`, `SEC`, `DB` | placeholder | — | — |

`ASYNC` has been promoted to an experiment. Try a theory with:

```bash
uv run python -m logger_lab.theories._test_theory TIMED_FILE
```

## Registry

| API | Import | Purpose |
| --- | --- | --- |
| `EXPERIMENTS`, `PROFILES`, `THEORIES` | `logger_lab.core` | Enum → factory dicts, filled at import through the `register_*` helpers. |
| `CHANNELS` | `logger_lab.core` | Experiment/theory → `Channel`. |
| `PROFILE_EXPERIMENTS` | `logger_lab.core` | Profile → its declared `ExperimentType`s, in order. |
| `register_experiment(exp_enum, fn, channel)` | `logger_lab.core` | Validates that `fn` is callable and takes a `level`, and that it is on `DISPATCH` exactly when it is a `@dispatcher`, then records it and its channel. Raises `ExperimentRegistrationError`. |
| `register_profile(profile_enum, fn, experiments)` | `logger_lab.core` | Validates `fn`, checks that every declared factory is a registered experiment and that no two share a channel, then records both. Raises `ProfileRegistrationError`. |
| `register_theory(theory_enum, fn, channel)` | `logger_lab.core` | The same as `register_experiment`, for a theory that works. |
| `get_experiment`, `get_profile`, `get_theory` | `logger_lab` | Lookups that raise `ExperimentNotFoundError`, `ProfileNotFoundError` or `TheoryNotFoundError` instead of `KeyError`. |
| `get_profile_experiments(p)`, `get_channel(e)` | `logger_lab.core` | Composition lookups used by the builder. |
| `find_channel_clash(entries)` | `logger_lab.core` | The single home of the one-per-channel rule. Returns `(first, second, channel)` or `None`. |
| `LabExperiment`, `LabProfile` | `logger_lab.core.registry` | `runtime_checkable` protocols documenting the factory shapes. |

## Logging kernel

| API | Import | Purpose |
| --- | --- | --- |
| `configure_handler(handler, level, formatter=None)` | `logger_lab.logging_kernel` | The shared experiment skeleton: sets the level and attaches the formatter if one is given. |
| `get_log_dir(path='logs')` | `logger_lab.logging_kernel` | The only place directories get created. Raises `LogDirectoryError`. |
| `clear_handlers(logger)` | `logger_lab.logging_kernel` | Detaches every handler and releases it (an atomic swap to an empty list). |
| `share_file_handler(path, *, kind, settings, open_handler, logger_name=None)` | `logger_lab.logging_kernel` | Returns the one handler for *path*, opening it only if nobody has it open. Applies the sharing rules above. Every file experiment and theory uses it. |
| `install_handlers(logger, factories, dispatcher=None)` | `logger_lab.logging_kernel` | Builds every handler (a *dispatcher* then wraps them), swaps the result onto *logger* in one assignment and releases the old ones. If a factory raises, the logger is left untouched. |
| `release_handler(handler, logger_name=None)` | `logger_lab.logging_kernel` | Gives up one logger's use of *handler*. Closes it when nobody uses it any more, and only if logger-lab created it. |
| `SharedFileHandler`, `SharedRotatingFileHandler`, `SharedTimedRotatingFileHandler`, `StayClosedMixin` | `logger_lab.logging_kernel` | File handlers that drop records after `close()` instead of reopening their file. |
| `AsyncHandler(targets, logger_name)` | `logger_lab.logging_kernel` | The one handler on an `async` logger: freezes each record, queues it, and delivers it to *targets* on the worker. Releasing it drains, then releases the targets. |
| `drain(timeout=None)` | `logger_lab` / `logger_lab.logging_kernel` | Waits until every queued record is written. `True` when empty, `False` on timeout or when called from the worker. |
| `stop_worker(timeout=5.0)` | `logger_lab.logging_kernel` | Drains, then stops the worker (run automatically at exit). The next record starts a new one. |
| `dispatcher`, `is_dispatcher(fn)` | `logger_lab.logging_kernel` | The decorator that marks a dispatcher factory, and the check the builder, `build_profile` and the registry use. |
| `RelayHandler`, `Subscriber` | `logger_lab.experiments.relay` | The handler that calls one subscriber (exceptions reported via `handleError`), and the callback type. |
| `SHARED_FILES`, `LAB_HANDLERS`, `file_key(path)` | `logger_lab.logging_kernel` | The table of open files (path → handler, kind, settings, owners), the weak set of handlers logger-lab created, and the normalized path key. |
| `JSONFormatter` | `logger_lab.logging_kernel` | Mosquito Lab Logging Standard v1.1: `timestamp` (UTC ISO-8601), `level`, `logger`, `message`, `source{module,function,line}`; `exception{type,message,traceback}` when there is one; `stack` with `stack_info=True`; `extra{...}` for any non-standard record attributes. v1.1 only adds fields to v1. |
| `build_file_formatter()` | `logger_lab.logging_kernel` | The formatter used by both file experiments. |
| `normalize_level_name`, `normalize_exp_name`, `normalize_profile_name`, `normalize_theory_name` | `logger_lab.logging_kernel` | Turn members or value strings into enums (and level names into numbers) for the builder; raise a typed error otherwise. |
| `default_level(plan)` | `logger_lab.core.builder` | The default-level rule: `WARNING` if `minimalist` is in the plan, else `INFO`. |
| `DEFAULT_LOG_DIR`, `DEFAULT_FILENAME`, `DEFAULT_ENCODING`, `DEFAULT_MAX_BYTES`, `DEFAULT_BACKUP_COUNT` | `logger_lab.logging_kernel.constants` | The defaults shared by `with_file_args()` and the file experiments. |

## Errors and warnings

All of these are importable from `logger_lab`.

```text
LabError
├── LabRegistryError
│   ├── ExperimentNotFoundError      valid ExperimentType, not registered
│   ├── ProfileNotFoundError         valid ProfileType, not registered
│   ├── TheoryNotFoundError          valid TheoryType, still a placeholder
│   ├── InvalidExperimentName        not a member or value of ExperimentType
│   ├── InvalidProfileName           not a member or value of ProfileType
│   └── InvalidTheoryName            not a member or value of TheoryType
├── LabConfigurationError
│   ├── InvalidLevelError            unknown level name, negative or non-integer level
│   ├── HandlerConfigurationError    handler failed to initialize
│   │   └── LogDirectoryError        mkdir/access failure in get_log_dir()
│   ├── ExperimentClashError         two experiments on one channel
│   ├── LogFileClashError            file already open as a different experiment
│   ├── ExperimentRegistrationError  bad factory passed to register_experiment/register_theory
│   └── ProfileRegistrationError     bad profile callable or clashing composition
└── BuilderError                     build() with nothing queued, or async with no output

DuplicateExperimentWarning (UserWarning)   same experiment twice, first kept
SharedFileSettingsWarning  (UserWarning)   shared file keeps its first settings
```

To make duplicates fatal in tests or CI, run with
`-W error::logger_lab.DuplicateExperimentWarning`, or use `warnings.simplefilter`.

## Writing a new experiment or theory

```python
from logging import DEBUG, Handler, StreamHandler
from logger_lab.logging_kernel import configure_handler

def my_experiment(level: int = DEBUG, **kwargs: object) -> list[Handler]:
    """One-line summary of what this handler does."""

    return [configure_handler(StreamHandler(), level, formatter=None)]
```

1. Use the `(level, **kwargs) -> list[Handler]` shape and accept `**kwargs`
   even if you ignore them.
2. Create directories only through `get_log_dir()`, and finish with
   `configure_handler()`. **A file experiment never opens its own file.** It
   asks `share_file_handler()` for it, passing a `kind`, the settings that must
   agree, and a `StayClosedMixin` handler at `NOTSET` (see `file.py`).
3. Decide its channel (console, file, JSON or live) and make sure it's thread-safe.
   A **dispatcher** (a new kind of `async`) is marked `@dispatcher`, takes
   `handlers=` (the built outputs) and returns what goes on the logger instead;
   it is registered on `Channel.DISPATCH`.
4. Theory: add a `TheoryType` value, then, once it works, call
   `register_theory(TheoryType.X, factory, Channel.Y)` at the bottom of
   `registry.py` and try it with the `_test_theory` harness.
5. Promote: move it into `experiments/`, add an `ExperimentType` value and add
   it to the experiment registration list with its channel.
