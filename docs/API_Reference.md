# logger-lab API Reference

## Scope and import policy

logger-lab is a composable layer over the standard-library `logging` module.
It never replaces `logging.Logger`: every entry point returns a plain stdlib
logger with handlers attached, so anything that works with `logging` keeps
working.

The top-level `logger_lab` package is the consumer-facing surface. Lower-level
building blocks are imported from their subpackages.

```python
from logger_lab import lab, log_event, drain, Output, Feature, Format, Catalyst, Unit, Day, ProfileType, LabError
from logger_lab.core import OUTPUTS, FEATURES, FeatureSpec, Kind, register_theory
from logger_lab.logging_kernel import configure_handler, get_log_dir, JSONFormatter, TimeRule
```

The builder's recorded state (`LabBuilder._outputs` and friends) is not
public API.

## The composition model

A logger is composed from **four kinds** of building block. Each kind has its
own builder method, its own enum and its own spec type.

| Kind | Method | Enum | Spec | Lives in | Answers |
| --- | --- | --- | --- | --- | --- |
| **Output** | `with_output(name, **options)` | `Output` | `OutputSpec` | `logger_lab/outputs/` | where does feedback go? |
| **Feature** | `with_feature(name, on=None, **options)` | `Feature` | `FeatureSpec` | `logger_lab/features/` | what extra does an output do? |
| **Format** | `with_format(name, on=None, **options)` | `Format` | `FormatSpec` | `logger_lab/formats/` | how does a record look? |
| **Catalyst** | `with_catalyst(name, **options)` | `Catalyst` | `CatalystSpec` | `logger_lab/catalysts/` | how does every record flow? |

Two more things compose them:

| | What it is | Where it lives |
| --- | --- | --- |
| **Profile** | A common composition, written as a recipe of builder calls (`ProfileSpec`) | `logger_lab/profiles/` |
| **Theory** | A building block of any kind, still being researched (`TheoryType`) | `logger_lab/theories/` |

### How the builder composes

```text
lab() ──► with_profile(...)           ┐  the profile's recipe runs here: it calls the
      ──► with_output(...)            │  same with_* methods (origin "from profile 'X'")
      ──► with_feature(..., on=)      │
      ──► with_format(..., on=)       │  recorded only, nothing built.  Asking for the
      ──► with_catalyst(...)          │  same building block again configures it:
      ──► with_theory(..., on=)       │  options merge, later values win
      ──► with_subscriber(cb, lvl)    │  (brings the relay output)
      ──► with_level(...)             ┘
      ──► plan()   1. nothing queued → BuilderError; only catalysts → CompositionError
                   2. each output: options merged over its spec's defaults (unknown → CompositionError)
                   3. each feature, then each format: attached to every queued output it fits,
                      or to on='s output; none fits → CompositionError naming the fix;
                      exclusive group (detail) / one format per output enforced; spec.check runs
                   4. each output: default format, feature–format fit, output spec.check
                   5. catalysts: options merged, one per group (dispatch)
                   6. no profile → ProfileSuggestionWarning if a profile already says this
      ──► build(name)
                   1. plan()  (fails before anything is touched)
                   2. each output's spec.build(OutputPlan) → its handlers; the file output gets
                      its handler from the shared file table
                   3. each catalyst, in order, wraps the built handlers (ASYNC → one AsyncHandler)
                   4. install_handlers(): one atomic swap onto getLogger(name), then the old
                      handlers are released (closed only when last, and only if logger-lab made them)
                   5. logger.setLevel(level or INFO); logger.propagate = False
```

### Composition rules

| Rule | Example that raises `CompositionError` |
| --- | --- |
| A feature or format never brings an output | `with_profile("observer").with_feature("ROTATING")` |
| `on=` must name a queued output the block fits | `with_feature("ROTATING", on="console")`, `with_format("JSON", on="file")` with no file |
| One detail feature (`MINIMAL` / `VERBOSE`) per output | `with_profile("observer").with_feature("VERBOSE")` |
| One format per output | `with_profile("ai_agent").with_format("TEXT")` |
| A detail feature needs `RICH` or `TEXT` | `with_profile("ai_agent").with_feature("MINIMAL")` |
| Options must be declared by the block, with valid values | `with_output("file", max_bytes=10)` (that is `ROTATING`'s) |
| One profile per builder | `with_profile("observer").with_profile("gui")` |
| One catalyst per group | `ASYNC` + a `PROCESS` theory (both `dispatch`) |

Every message says how to fix the composition.

**Profile suggestion.** `plan()` warns `ProfileSuggestionWarning` when no
profile is used, two or more outputs were queued, and a profile says the same
thing. The suggestion is tested before it is made. The hand-made composition is
replayed on top of the profile, and the result must plan to exactly the same
composition. So following it never adds anything and never leads to a clash.
The most specific such profile is named. File + relay alone does not suggest
`gui`, which would add `ROTATING` and `ASYNC`. A minimal console beside a
verbose file does not suggest `conspiracy_theorist`, whose `VERBOSE` would
also reach the console.

**Profiles pin with `on=`.** A recipe targets its features and formats at its
own outputs wherever an output added later could also take them. For example,
`ai_agent`'s `JSON` stays on the console when a file is added on top.

### Across loggers: one file, one handler

Within a logger there is one output of each kind. Across loggers, every log
file has exactly one handler in the process (`share_file_handler()`), so each
module can pick its own composition and level and still write to one `app.log`.

The file's **kind** must match to share. The kind is the format plus the
rotation features, e.g. `FILE[TEXT]`, `FILE[JSON]+ROTATING` or
`FILE[TEXT]+ROTATING+TIMED`. Its **settings** should match too: `encoding`,
`backup_count`, `detail`, `max_bytes`, `every`, `unit`, `day`, `at` and `utc`.

| A second logger asks for an open file with… | Result |
| --- | --- |
| the same kind and settings | shares the handler |
| the same kind, different settings | shares it with the **first** settings + `SharedFileSettingsWarning` |
| a different kind (`FILE[TEXT]` vs `FILE[TEXT]+ROTATING`, `TEXT` vs `JSON`) | `LogFileClashError` (use another `filename`) |
| …and it's the file's only logger, being rebuilt | a new handler replaces the old one |

Shared file handlers have no level of their own (`NOTSET`). Each logger's level
filters its own records. The file closes when its last logger releases it.

### Thread safety

Every output, feature and profile is thread-safe within one process:
- **Writes:** handlers lock each write, and formatters hold no state.
- **Files:** one handler per file, created under a lock. Rollover happens under
  the handler's lock.
- **Building:** `build()` swaps a logger's handlers in one assignment, so a
  thread that's logging finishes its record on the old list. Released file
  handlers stay closed (`StayClosedMixin`) and never reopen.
- **Async:** one queue and **one worker thread for the whole process**, however
  many loggers use `ASYNC`. Records keep their order; a record's message is fixed
  on the calling thread; queued records are written before exit (`stop_worker`
  runs at exit, before `logging.shutdown`). Exit and releasing an async logger
  each wait at most `DRAIN_TIMEOUT` (5 s), so a stuck subscriber can't hang
  them. A relay subscriber runs outside its handler's lock, which
  `logging.shutdown` takes.
- **Builders:** a single `LabBuilder` instance is not meant to be shared
  between threads while it is being configured.
- **Processes:** several processes writing one file is not covered.

### Async dispatch

The full picture (record flow, limits, Qt, asyncio, Tkinter) is in `Feedback_Guide.md`.

| | Without `ASYNC` | With `ASYNC` |
| --- | --- | --- |
| Who formats and writes | the thread that logged | the `logger-lab-dispatch` worker |
| Caller cost per written file record (measured on Windows, 2026-10-23) | ~25 µs | ~13 µs, and never waits on a slow disk |
| Tracebacks (`logger.exception`) | written | written (unlike the stdlib `QueueHandler`) |
| A subscriber runs on | the thread that logged | the worker |
| Wait for everything queued | n/a | `drain(timeout=None)`, from `logger_lab` |

`drain()` called from the worker itself (say, inside a subscriber) returns `False`
at once instead of waiting on itself. Releasing an async logger waits for its
queued records, then releases its outputs.

## Entry points

| API | Import | Purpose |
| --- | --- | --- |
| `lab()` | `logger_lab` | Returns a fresh `LabBuilder`. **The one way to build a logger.** There is no separate one-call shortcut. |
| `log_event(logger, level, msg, *, event, context=None, tags=None)` | `logger_lab` | Emits one structured record (`event`, `context`, `tags` in `extra`). Pairs with the `JSON` format and the `ai_agent` profile. |
| `drain(timeout=None)` | `logger_lab` | Waits until every record queued by `ASYNC` is written. |
| `__version__` | `logger_lab` | The installed version (`"0.2.0"`), read from the package metadata. |

```python
import logging
from logger_lab import lab, Feature

logger = lab().with_profile("investigator").build(__name__)

logger = (
    lab()
    .with_profile("investigator")
    .with_output("file", log_dir="run_logs", filename="session.log")
    .with_feature(Feature.TIMED, at="02:00")
    .with_level("DEBUG")
    .build(__name__)
)
```

## Names: member or value

Everything is selectable by its enum **member** or its **value string**,
case-insensitively, in every entry point (`on=` too). The member *name* as a
string is not an alias. A name from another kind is rejected: `with_output("ROTATING")`
raises `InvalidNameError` (whose `.kind` is `"output"`), listing the valid names.

| Member | Value string | ✔ accepted | ✘ rejected |
| --- | --- | --- | --- |
| `ProfileType.AGENT` | `"AI_AGENT"` | `ProfileType.AGENT`, `"AI_AGENT"`, `"ai_agent"` | `"AGENT"` |
| `ProfileType.CONSPIRATOR` | `"CONSPIRACY_THEORIST"` | `ProfileType.CONSPIRATOR`, `"conspiracy_theorist"` | `"CONSPIRATOR"` |
| every other member | same as its name | member, value, lowercase value | none |

## `LabBuilder`

Every `with_*` method only records state and returns `self`. Nothing is built
and no files are opened until `build()`.

| Method | Purpose |
| --- | --- |
| `with_output(output, **options)` | Adds an `Output`. If the logger already has it (from a profile, say), it configures it instead. Options merge per key; later values win. A logger holds at most one output of each kind. |
| `with_feature(feature, on=None, **options)` | Adds a `Feature` to every queued output it fits, or only to *on*. Repeats merge options. |
| `with_format(format_, on=None, **options)` | Sets the `Format` of every queued output it fits, or only of *on*. |
| `with_catalyst(catalyst, **options)` | Adds a `Catalyst`. Repeats merge options (one `ASYNC`, never two queues). |
| `with_profile(profile)` | Runs the profile's recipe on this builder. One per builder; a second raises `CompositionError`. Add or configure on top afterwards. |
| `with_theory(theory, on=None, **options)` | Adds a registered `TheoryType` as the kind it was registered as (`on=` for a feature or format theory). A placeholder raises `TheoryNotFoundError`. `on=` with an output or catalyst theory raises `CompositionError`. |
| `with_subscriber(callback, level=None)` | Adds a subscriber: *callback* gets every record that passes *level* (`None` → the logger's level). Brings the `relay` output with it. Each call adds another. The record is shared; treat it as read-only. |
| `with_level(level)` | Sets the logger's level, the one switch: every handler is `NOTSET`. Level names (case-insensitive, custom ones too) or integers `0` or above; anything else raises `InvalidLevelError`. If never called: **INFO**, for every logger. |
| `plan()` | Checks the composition and returns a `Composition` (`.outputs`: `PlannedOutput`s in queue order; `.catalysts`; `.names()`: a compact summary). Builds nothing. |
| `build(name)` | Plans, then builds the logger (see the composition model above). Returns a stdlib `Logger` with `propagate = False`. |

## Outputs

| `Output` | Options (defaults) | Formats | Built | Notes |
| --- | --- | --- | --- | --- |
| `CONSOLE` | `stream="stderr"` (or `"stdout"`) | `RICH` (default), `TEXT`, `JSON` | `LabRichHandler` (a `RichHandler`) for `RICH`, else `StreamHandler` | Level `NOTSET`, so the logger's level is the one switch. Rich markup in messages is off; `extra={"markup": True}` turns it on for one record. A failure is reported, never raised |
| `FILE` | `log_dir="logs"`, `filename="app.log"`, `encoding="utf-8"`, `backup_count=3` | `TEXT` (default), `JSON` | the shared `LabFileHandler` | `log_dir` is created (parents too) by `get_log_dir()` on build. `backup_count` must be ≥ 0, and ≥ 1 with a rotation feature |
| `RELAY` | none | none | `RelayHandler`, one per subscriber (none without subscribers) | A callback that raises is reported, never propagated. A record logged inside a subscriber is not relayed again |

## Features

| `Feature` | Fits | Group | Formats | Options (defaults) | Effect |
| --- | --- | --- | --- | --- | --- |
| `MINIMAL` | console, file | detail | `RICH`, `TEXT` | none | Level and message only (Rich: no time column) |
| `VERBOSE` | console, file | detail | `RICH`, `TEXT` | none | Adds `module.function:line` (Rich: the path column and the logger name) |
| `ROTATING` | file | none | any | `max_bytes=5_242_880` | Roll over before a record would reach *max_bytes*, counted in bytes as written (encoding, line endings). The stdlib counts characters |
| `TIMED` | file | none | any | `every=1`, `unit=None` (day), `day=None`, `at=None`, `utc=False` | Roll over at the start of every period |

No detail feature → **standard** detail: time, level and message (plus the
logger name in `TEXT`).

| Detail | `TEXT` layout |
| --- | --- |
| minimal | `%(levelname)s: %(message)s` |
| standard | `%(asctime)s - %(name)s - %(levelname)s - %(message)s` |
| verbose | `%(asctime)s - %(name)s - %(levelname)s - %(module)s.%(funcName)s:%(lineno)d - %(message)s` |

### `TIMED` in detail

The options follow the `schedule` package, as keyword arguments:
`with_feature("TIMED", every=6, unit="hours")` is `schedule.every(6).hours`.

| Option | Values | Meaning |
| --- | --- | --- |
| `every` | a whole number, 1 or more (default 1) | How many units make a period. A unit on its own means one of it: `unit="hour"` is every hour |
| `unit` | a `Unit` member, or `"minute"`, `"hour"`, `"day"`, `"week"`, `"month"` or the plural; case-insensitive | The unit. Default: `"week"` with a `day`, otherwise `"day"` |
| `day` | a `Day` member, or `"monday"` … `"sunday"`; or `None` | The day a week starts. It needs a weekly unit (or none given) |
| `at` | `":MM"` for an hour; `"HH:MM"` or a `datetime.time` for a day, week or month; `None` | When a period starts. Not allowed for a minute |
| `utc` | `True` / `False` | Boundaries and labels in UTC instead of local time: the same moment on every machine, and no repeated or missing hour at a daylight-saving change |

Periods are anchored to the calendar, not to when the app started. Minutes,
hours, days and weeks count from Monday 1970-01-05 at midnight, and months
count from January. So `every=6, unit="hours"` rolls over at 00:00, 06:00,
12:00 and 18:00, and `every=3, unit="months"` gives quarters. A restart never
moves the schedule. `schedule` itself counts from the start and has no month
unit; logger-lab differs on both points on purpose.

An existing file belongs to the period it was last modified in, so restarting
after a few days rolls the old file into its own label.

### Backup names (`LabFileHandler`)

| Features | Scheme | Retention |
| --- | --- | --- |
| `ROTATING` | `app.log.1` (newest) … `app.log.N`, the stdlib shift | `backup_count` numbered files |
| `TIMED` | `app.log.<label>`: `2026-10-22`, `2026-10` (month), `2026-10-22_14` (hour), `2026-10-22_14-30` (minute) | the newest `backup_count` labeled backups |
| both | `app.log.<label>.1`, `.2` … within a period | the newest `backup_count` pieces |

A backup is never overwritten: a taken label gets a counter. The stdlib
`TimedRotatingFileHandler` deletes it instead, and it has no monthly rotation.
That is why the rules live in `logging_kernel/rollover.py`. Pruning only
touches names of the labeled form, so numbered backups and other files are
left alone.

## Formats

| `Format` | Fits | Output |
| --- | --- | --- |
| `RICH` | console | Rich columns, colors and Rich tracebacks |
| `TEXT` | console, file | The detail's text layout |
| `JSON` | console, file | `JSONFormatter`: one object per line (JSON lines on a file) |

## Catalysts

| `Catalyst` | Group | Options | Built |
| --- | --- | --- | --- |
| `ASYNC` | dispatch | none | One `AsyncHandler` wrapping the built outputs; `BuilderError` if they built nothing (a relay with no subscribers) |

## Profiles

| `ProfileType` | Value | Recipe | Use case |
| --- | --- | --- | --- |
| `OBSERVER` | `"OBSERVER"` | console + `MINIMAL` (on console) | Low noise. Raise the level for production: `.with_level("WARNING")` |
| `INVESTIGATOR` | `"INVESTIGATOR"` | console + file | Everyday development |
| `CONSPIRATOR` | `"CONSPIRACY_THEORIST"` | console + file + `VERBOSE` + `ROTATING` | Capture everything, rotated |
| `AGENT` | `"AI_AGENT"` | console + `JSON` (on console) | Structured JSON for pipelines and LLMs |
| `GUI` | `"GUI"` | file + `ROTATING` + relay + `ASYNC` | Desktop apps (LabFrame): no console, file and subscribers off the calling thread |

A recipe is `(builder) -> builder` and only calls the builder, so a profile
obeys every composition rule. The test suite plans every profile, so a
recipe that breaks a rule fails the tests.
There are no profile functions: `lab().with_profile(...)` is the way in.

## Theories

| Stage | What exists | Registered? | Selecting it |
| --- | --- | --- | --- |
| Idea | `theories/name_exp.py` with the plan and its likely kind in its docstring | No | n/a |
| Placeholder | Plus a `TheoryType` value | No | `TheoryNotFoundError` |
| Trial | A working spec of some kind, registered with `register_theory(kind, spec)` | Yes | `with_theory()`. It acts as its kind |
| Promoted | Moved into its kind's package with that kind's enum value. A helper joins the public API instead, beside `log_event` | As that kind | its kind's method, or the helper itself |

| `TheoryType` | Stage |
| --- | --- |
| `TRACE`, `LIFECYCLE`, `THROTTLE`, `PERFORMANCE`, `PROCESS`, `HTTP`, `SEC`, `DB` | placeholder (roadmap order: `Continuation.md` §3) |

`TIMED_FILE` has been promoted to the `TIMED` feature. Try a registered
theory by adding it to a builder, as the tests do:

```python
lab().with_profile("gui").with_theory("THROTTLE").build(__name__)
```

## Registry

| API | Import | Purpose |
| --- | --- | --- |
| `OUTPUTS`, `FEATURES`, `FORMATS`, `CATALYSTS`, `PROFILES` | `logger_lab.core` | Member → spec tables, written out in `core/registry.py`. Tests pin that they are well formed. Each spec sits under its own member; a feature or format fits an output; an output renders its default format; a format fits exactly the outputs that render it. The tests also plan every profile. |
| `THEORIES` | `logger_lab.core` | `TheoryType` → `(Kind, spec)`, the one table filled at runtime. |
| `register_theory(kind, spec)` | `logger_lab.core` | Checks the spec as it comes in (its type matches *kind*, its member is a `TheoryType`, `build` is callable, it fits an output), then adds it. Raises `RegistrationError`. |
| `spec_for(member)`, `get_theory(theory)`, `get_profile(profile)` | `logger_lab.core` | Lookups that raise `RegistrationError` / `TheoryNotFoundError` instead of `KeyError`. |

### Specs

| Spec | Fields |
| --- | --- |
| `OutputSpec` | `member`, `build(OutputPlan) -> list[Handler]`, `options`, `formats` (the formats it renders; another raises `CompositionError`), `default_format`, `check(OutputPlan)` |
| `FeatureSpec` | `member`, `fits`, `options`, `group`, `formats` (`None` = any), `check(options) -> options` |
| `FormatSpec` | `member`, `fits`, `options` |
| `CatalystSpec` | `member`, `build(handlers, *, logger_name, options) -> list[Handler]`, `options`, `group` |
| `ProfileSpec` | `member`, `recipe(builder) -> builder`, `summary` |
| `OutputPlan` | what an output's `build` gets: `output`, `options`, `features`, `format`, `format_options`, `logger_name`, `subscribers`; `.detail` → `"minimal"` / `"standard"` / `"verbose"` |

## Logging kernel

| API | Import | Purpose |
| --- | --- | --- |
| `configure_handler(handler, level, formatter=None)` | `logger_lab.logging_kernel` | Sets the level, attaches the formatter if one is given, and marks the handler as logger-lab's (`LAB_HANDLERS`). |
| `get_log_dir(path='logs')` | `logger_lab.logging_kernel` | The only place directories get created. Raises `LogDirectoryError`. |
| `clear_handlers(logger)` | `logger_lab.logging_kernel` | Detaches every handler and releases it (an atomic swap to an empty list). |
| `share_file_handler(path, *, kind, settings, open_handler, logger_name=None)` | `logger_lab.logging_kernel` | Returns the one handler for *path*, opening it only if nobody has it open. Applies the sharing rules above. |
| `install_handlers(logger, factories, dispatcher=None)` | `logger_lab.logging_kernel` | Builds every handler (a *dispatcher* then wraps them), swaps the result onto *logger* in one assignment and releases the old ones. If a factory raises, the logger is left untouched. |
| `release_handler(handler, logger_name=None)` | `logger_lab.logging_kernel` | Gives up one logger's use of *handler*. Closes it when nobody uses it any more, and only if logger-lab created it. |
| `LabFileHandler(filename, *, encoding, backup_count, size=None, schedule=None)` | `logger_lab.logging_kernel` | The one file handler: plain, by size, on a schedule, or both (naming above). A `StayClosedMixin` `BaseRotatingHandler`. |
| `SizeRule(max_bytes)`, `TimeRule(every=1, unit="day", day=None, at=None, utc=False)`, `UNITS`, `DAYS` | `logger_lab.logging_kernel` | The rollover rules: `TimeRule.period_start`, `.next_boundary`, `.label`. |
| `StayClosedMixin` | `logger_lab.logging_kernel` | Drops records after `close()` instead of reopening the file. |
| `AsyncHandler(targets, logger_name)` | `logger_lab.logging_kernel` | The one handler on an `ASYNC` logger: freezes each record, queues it, and delivers it to *targets* on the worker. Releasing it drains, then releases the targets. |
| `drain(timeout=None)` | `logger_lab` / `logger_lab.logging_kernel` | `True` when everything queued is written, `False` on timeout or when called from the worker. |
| `stop_worker(timeout=None)`, `DRAIN_TIMEOUT` | `logger_lab.logging_kernel` (`DRAIN_TIMEOUT` lives in, and is set on, `logger_lab.logging_kernel.dispatch`) | Drains, then stops the worker, within one deadline (`DRAIN_TIMEOUT`, 5 s, by default; run automatically at exit). Each worker has a generation, so one replaced while stuck finishes its record and exits: two never deliver at once. Releasing an `AsyncHandler` waits for its own records within the same limit. The next record starts a new one. |
| `RelayHandler`, `Subscriber` | `logger_lab.outputs.relay`, `logger_lab.core.specs` | The handler that calls one subscriber (exceptions reported via `handleError`), and the callback type. |
| `SHARED_FILES`, `LAB_HANDLERS`, `file_key(path)` | `logger_lab.logging_kernel` | The table of open files (path → handler, kind, settings, owners), the weak set of handlers logger-lab created, and the normalized path key. |
| `JSONFormatter` | `logger_lab.logging_kernel` | Mosquito Lab Logging Standard v1.2: `timestamp` (`DATE_FORMAT`, local time, like the text format), `level`, `logger`, `message`, `source{module,function,line}`; `exception{type,message,traceback}` when there is one; `stack` with `stack_info=True`; `extra{...}` for any non-standard record attributes. v1.1 added `logger`, `exception` and `stack` to v1. v1.2 writes `timestamp` like the text format (v1.1 used UTC ISO-8601). |
| `text_formatter(detail="standard")`, `TEXT_LAYOUTS`, `DATE_FORMAT` | `logger_lab.logging_kernel` | The `TEXT` format's layouts. |
| `normalize_name(enum_type, value, kind)`, `normalize_level_name(level)`, `level_names()` | `logger_lab.logging_kernel` | Turn members or value strings into enums (and level names into numbers); raise `InvalidNameError` / `InvalidLevelError` otherwise. |
| `DEFAULT_LOG_DIR`, `DEFAULT_FILENAME`, `DEFAULT_ENCODING`, `DEFAULT_MAX_BYTES`, `DEFAULT_BACKUP_COUNT` | `logger_lab.logging_kernel.constants` | The defaults of the file output and `ROTATING`. |

## Errors and warnings

All of these are importable from `logger_lab`.

```text
LabError
├── LabRegistryError
│   ├── InvalidNameError             not a member or value of that kind's enum (.kind says which)
│   ├── TheoryNotFoundError          valid TheoryType, still a placeholder
│   └── RegistrationError            a malformed theory spec, or a lookup that finds nothing
├── LabConfigurationError
│   ├── InvalidLevelError            unknown level name, negative or non-integer level
│   ├── CompositionError             a composition that can't work; the message says how to fix it
│   ├── HandlerConfigurationError    handler failed to initialize
│   │   └── LogDirectoryError        mkdir/access failure in get_log_dir()
│   └── LogFileClashError            file already open with a different kind
└── BuilderError                     build() with nothing queued, or ASYNC with nothing built to wrap

ProfileSuggestionWarning   (UserWarning)   a hand-made composition a profile already says
SharedFileSettingsWarning  (UserWarning)   shared file keeps its first settings
```

To make suggestions fatal in tests or CI, run with
`-W error::logger_lab.ProfileSuggestionWarning`, or use `warnings.simplefilter`.

## Writing a new building block

A building block is a spec. For example, a feature:

```python
from logger_lab.core.enums import Output, TheoryType
from logger_lab.core.specs import FeatureSpec

THROTTLE_SPEC = FeatureSpec(
    member=TheoryType.THROTTLE,
    fits=frozenset({Output.RELAY}),
    options={"per_second": 20},
    check=check_throttle,     # validates/normalizes options; raise CompositionError
)
```

1. Pick its kind. An **output** builds handlers from an `OutputPlan`; a
   **feature** or **format** is data the outputs it fits interpret (teach the
   output's `build` about it); a **catalyst** wraps the built handlers.
2. Create directories only through `get_log_dir()`, and finish handlers with
   `configure_handler()`. **A file handler is never opened directly**: ask
   `share_file_handler()` for it, passing a `kind`, the settings that must
   agree, and a `StayClosedMixin` handler at `NOTSET` (see `outputs/file.py`).
3. Declare every option with its default, and unknown options are rejected
   for you. Validate values in `check`, raising `CompositionError`. Make sure
   it is thread-safe.
4. Theory: add a `TheoryType` value. Once it works, call
   `register_theory(Kind.FEATURE, THROTTLE_SPEC)` and try it with
   `lab().with_profile(...).with_theory("THROTTLE")` in a test.
5. Promote: move it into its kind's package, give it a member of that kind's
   enum, and add its spec to that kind's table in `core/registry.py`.
