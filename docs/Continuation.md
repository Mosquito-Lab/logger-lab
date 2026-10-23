# Continuation Doc: logger-lab

**Purpose:** self-contained context for continuing logger-lab in a fresh
conversation. Read it cold and pick up from "Next immediate action" at the
bottom. This doc owns the roadmap, the theory pipeline, locked-in decisions,
and what is built and what isn't. The rules live in `Standards_and_Tracker.md`.
Every finding ID used here (`PF-1`, `KN-1` and so on) is defined in
`Cleanliness_Tracker.md`.

**Last updated:** 2026-10-23

---

## 1. Where logger-lab sits

- **logger-lab** (`v0.2.0`, Python ≥ 3.10, only dependency `rich`): a
  composable layer over stdlib `logging`: four kinds of building block
  (outputs, features, formats, catalysts), profiles as recipes of them, and one
  builder. See the API Reference.
- **LabFrame**: the PySide6 framework, and logger-lab's first real consumer
  (`LabFrame.feedback.channel` calls
  `get_logger("LabFrame.feedback", experiment=ExperimentType.ROTATING_FILE)`,
  which 0.2.0 removes. See the LabFrame adoption step in §5.)
  LabFrame's Standards doc keeps a list of logger-lab gaps found while
  integrating it; they are tracked here in §5.

---

## 2. Built (the stable core)

| Area | Status | Notes |
| --- | --- | --- |
| The four kinds (D-21): outputs `console`, `file`, `relay`; features `MINIMAL`, `VERBOSE`, `ROTATING`, `TIMED`; formats `RICH`, `TEXT`, `JSON`; catalyst `ASYNC` | **Done 2026-10-22** | Each a spec (`core.specs`) next to its code; one builder method per kind; options on the blocks (D-25). |
| Profiles: `observer`, `investigator`, `conspiracy_theorist`, `ai_agent`, `gui` | **Done 2026-10-22** | Recipes of builder calls, planned by the tests. |
| Registry, as plain tables, with typed lookup errors | **Done 2026-10-23** | The built-in specs are written out; the tests pin that they are well formed. `register_theory()` checks a theory as it comes in. |
| `LabBuilder` / `lab()` | **Done** | The only composer (D-19). `plan()` holds every composition rule (D-23). |
| Rotation | **Done 2026-10-22** | `LabFileHandler` + `logging_kernel/rollover.py`: size, schedule or both; backups never overwritten (D-26). |
| `JSONFormatter` + `log_event()`, Mosquito Lab Logging Standard v1.2 | **Done** | v1.1 added `logger`, `exception` and `stack` (`KN-11`, `KN-17`); v1.2 writes `timestamp` like the text format; `log_event()` attributes records to its caller (`KN-10`). On a file: JSON lines. |
| Error hierarchy (`LabError` …) | **Done** | `InvalidNameError`, `RegistrationError`, `CompositionError`, `ProfileSuggestionWarning`; `InvalidLevelError` for invalid levels (`KN-2`). |
| Name resolution (enum member or value string) | **Done** | Every kind, profiles, theories and `on=`, case-insensitive; pinned by `tests/test_names.py`. |
| Tests + type check | **Done** | 190 tests (redesigned 2026-10-23: relevant behavior and edge cases, each fix shown to fail without it); pyrefly clean; Python 3.10, 3.13 and 3.14. |
| One file, one handler across loggers; thread safety | **Done 2026-10-22** | `share_file_handler()` keyed by kind, atomic `install_handlers()`, stay-closed file handlers (`CR-9`, `CR-10`, `TS-4`). |
| British-to-American spelling pass (`normalisers` → `normalizers`, etc.) | **Done, 2026-10-22** | Shipped in 0.2.0. |
| Cleanliness passes, round 1 | **Done 2026-10-23** | All eight passes closed and every finding fixed (`Cleanliness_Tracker.md`). |

### 0.2.0 changes (2026-10-22)

The public changes since 0.1.1 (Standards §3.3), as 0.2.0 now stands.
**Breaking** items need consumer action. 0.2.0 is unpublished, so anything
that existed only between releases (`with_log_dir()`, `with_file_args()`,
channels, `ExperimentClashError`, `DuplicateExperimentWarning`, the
`TIMED_FILE` trial, `build_profile`) is not listed as a change.

| Change | Breaking? | What a consumer does |
| --- | --- | --- |
| **Experiments become four kinds** (D-21): `with_experiment()` and `ExperimentType` are gone; `with_output()`, `with_feature()`, `with_format()`, `with_catalyst()` and `Output`, `Feature`, `Format`, `Catalyst` replace them | **Yes** | See the migration table below. |
| **`get_logger()` removed.** `lab()` is the only composer (D-19) | **Yes** | `get_logger(name, profile="investigator", level="DEBUG")` → `lab().with_profile("investigator").with_level("DEBUG").build(name)`. |
| Profile functions (`investigator(name)` …) removed; profiles are recipes (`ProfileSpec`) | **Yes** | `lab().with_profile("investigator").build(name)`. |
| One default level: **INFO**, for every logger (D-22). `observer` was WARNING | **Yes** | Call `.with_level("WARNING")` for a quiet observer. **LabFrame:** its DEBUG feedback lines need `.with_level("DEBUG")` (§5). |
| Invalid levels raise `InvalidLevelError` (a typo like `"DEBG"` used to become INFO silently) | **Yes** | Fix the level name. |
| Composition rules (D-23): features never bring outputs; one detail feature and one format per output; undeclared options rejected. All are `CompositionError` | **Yes** | Follow the message: it names the fix. |
| Hand-composing a profile warns `ProfileSuggestionWarning` (D-24) | New | Use the profile, or silence the warning. |
| Names: `InvalidExperimentName` / `InvalidProfileName` / `InvalidTheoryName` → `InvalidNameError` (with `.kind`); `ExperimentNotFoundError` / `ProfileNotFoundError` / `*RegistrationError` → `RegistrationError` | **Yes** | Catch the new names (or `LabRegistryError`). |
| `logging_kernel.normalisers` → `normalizers`; `normalize_exp_name` & co. → `normalize_name(enum, value, kind)` | **Yes** | Update the import. |
| `build_console_formatter()` / `build_file_formatter()` removed | **Yes** | Use `text_formatter(detail)` or `logging.Formatter`. |
| A file already open with another kind (format or rotation) raises `LogFileClashError` | **Yes** | Give one its own `.with_output("file", filename=...)`. |
| `conspiracy_theorist` is console + file + `VERBOSE` + `ROTATING` (one file, no duplicate records); `ai_agent` is console + `JSON` | Behavior | Nothing. |
| File handlers are one shared `LabFileHandler` per path (a `FileHandler` subclass) at level `NOTSET` | Behavior | Code checking `type(h) is FileHandler` should use `isinstance`. A logger's level does the filtering. |
| The Rich console writes to **stderr** by default, like the plain ones always did (0.1.1's `standard` wrote to stdout) | Behavior | `.with_output("console", stream="stdout")` if you relied on stdout. |
| `observer` and the `MINIMAL` / `VERBOSE` console are Rich now (0.1.1's `minimalist` / `verbose` were plain text) | Behavior | Add `.with_format("TEXT")` for the plain lines. |
| The verbose text line is `time - name - level - module.function:line - message` | Behavior | Update log parsers. |
| `clear_handlers()` releases handlers (shared files stay open while used) and never closes handlers logger-lab didn't create | Behavior | Nothing. |
| The Rich console prints brackets as text (markup off), and its handler is `NOTSET` like every other | Behavior | For styled text, pass `extra={"markup": True}` on that record. A `logger.setLevel()` after the build now reaches the console. |
| A logging call never raises: a bad format or a failing output is reported, and the other outputs still get the record | Fix | Nothing. |
| A record logged inside a subscriber is not relayed to subscribers (`EX-7`) | Behavior | Nothing, usually. Call another subscriber directly if it must know. |
| Exit and releasing an async logger wait at most `DRAIN_TIMEOUT` (5 s) for queued records; a stuck subscriber can't hang them (`KN-36`) | Fix | Nothing. Records still queued after the limit are lost. |
| `ROTATING`'s `max_bytes` counts bytes as written, not characters (`KN-39`) | Behavior | Nothing. With non-ASCII text or UTF-16, files now stay under the cap. |
| The registry is plain tables: `register_output`, `register_feature`, `register_format`, `register_catalyst`, `register_profile`, `check_spec` and `check_profiles` are gone (`register_theory` stays) | New in 0.2.0 | Nothing for a consumer. A contributor adds a built-in to its table. |
| An output refuses a format it can't render (`CR-17`) | Fix | Nothing. |
| `log_event()` records the caller as `source` | Fix | Nothing. |
| A shared file with different settings warns (`SharedFileSettingsWarning`) | New | Optionally make it an error in CI. |
| `TIMED` (`every=`, `unit=`, `day=`, `at=`, `utc=`, in the style of `schedule`; the `Unit` and `Day` enums), size + time together, JSON lines on a file (D-26, D-27) | New | `.with_feature("TIMED", at="02:00")`, `.with_format("JSON", on="file")`. |
| `ASYNC` catalyst and `drain()` | New | `.with_catalyst("ASYNC")` moves writing off the calling thread. |
| `relay` output and `with_subscriber(callback, level=None)` | New | Replace a hand-written callback/Qt handler with a subscriber. |
| `gui` profile: file + `ROTATING` + relay + `ASYNC`, no console | New | LabFrame: see §5. |
| `plan()`, `on=`, `with_theory(theory, on=None, **options)`, `register_theory()`, `py.typed`, `logger_lab.__version__` | New | Nothing. |
| Thread-safe by default (Standards §2.4) | New | Nothing. |
| JSON: Mosquito Lab Standard **v1.2**. v1.1 added `logger`, `exception{type,message,traceback}` and `stack`; v1.2 writes `timestamp` as `2026-10-22 23:35:41`, local time, like the text format (v1 used UTC ISO-8601) | **Yes**, for `timestamp` | A consumer that parsed the UTC ISO timestamp parses `DATE_FORMAT` instead. The other v1 fields are unchanged. |
| `main.py` and `src/__init__.py` deleted; docs moved to a repo-root `docs/` (no longer in the wheel) | Packaging | Nothing. |
| `rich>=12.6.0`; 0.1.1 required 15.0.0 (`PK-12`: the suite passes on Rich 12.6 to 15) | Packaging | Nothing. Projects on an older Rich can install it. |
| The `theories/_test_theory.py` harness is removed (`TH-4`): a theory is tried with `with_theory()` in a test | Removed | Nothing for a consumer; it was never public API. |

### Migration from 0.1.1

| 0.1.1 | 0.2.0 |
| --- | --- |
| `get_logger(name, profile="investigator")` | `lab().with_profile("investigator").build(name)` |
| `get_logger(name, experiment=ExperimentType.ROTATING_FILE)` | `lab().with_output("file").with_feature("ROTATING").build(name)` |
| `with_experiment("STANDARD")` | `with_output("console")` |
| `with_experiment("MINIMALIST")` | `with_output("console").with_format("TEXT").with_feature("MINIMAL").with_level("WARNING")`. Or, in Rich, `with_profile("observer")` |
| `with_experiment("VERBOSE")` | `with_output("console").with_format("TEXT").with_feature("VERBOSE")`. Or drop `TEXT` for Rich |
| `with_experiment("FILE")` | `with_output("file")` |
| `with_experiment("ROTATING")` | `with_output("file").with_feature("ROTATING")` |
| `with_experiment("AI")` | `with_output("console").with_format("JSON")` (or `with_profile("ai_agent")`) |
| `with_experiment("STANDARD").with_experiment("FILE")` | `with_profile("investigator")` |
| file args (`log_dir=`, `filename=`, `encoding=`, `backup_count=`) | `with_output("file", log_dir=..., filename=..., encoding=..., backup_count=...)` |
| `max_bytes=` | `with_feature("ROTATING", max_bytes=...)` |
| `observer` at WARNING | `with_profile("observer").with_level("WARNING")` |
| `investigator(name)` (profile function) | `lab().with_profile("investigator").build(name)` |

Verified for the redesign (2026-10-22): 281 tests pass, pyrefly is clean, and
every README example runs on its own with warnings as errors. The `gui` profile
was re-checked in LabFrame's own environment with real PySide6 (6.11.2).
Records logged on a worker thread and on the GUI thread went through a child
channel logger. All of them reached a Qt slot **on the GUI thread**, and the
file.

---

## 3. Roadmap

The order is deliberate. **Foundations come before new theories.** Phase 1 laid
them in 0.2.0, and the cleanliness passes bring every module up to the
standard before new theories land on it.

### Phase 1: foundations (do first, one step at a time)

Each step is proposed, approved, done, verified, and then recorded in
`Cleanliness_Tracker.md`.

| Step | Task | Findings | Open decisions | Status |
| --- | --- | --- | --- | --- |
| 0 | Test and type-check baseline: `uv_build`, a `dev` group (pytest, pyrefly), `tests/`, `py.typed`, root `.gitignore` | `PK-3`, `TS-1`, `PK-6` | none | **Done 2026-10-22**: 97 passed, pyrefly 0 errors |
| 1 | `conspiracy_theorist` becomes `verbose` + `rotating_file` only | `PF-1`, `EX-5` | none | **Done**: rotation verified on Windows |
| 2 | `clear_handlers()` closes the handlers it detaches | `KN-1` | none | **Done**. The builder no longer hands handlers over from the profile, so nothing moved gets closed. |
| 3 | One experiment per channel (console, file, JSON); clash → `ExperimentClashError`; duplicate → `DuplicateExperimentWarning`, first kept | `CR-1` (+ `CR-8` as a side effect) | D-7, settled | **Done**. Two *loggers* sharing a file stays open as `CR-9`. |
| 4 | Enum and value names pinned for every member; README and docs corrected | `DOC-1` | Case-insensitive: kept | **Done** |
| 5 | Theory rework: `register_theory()`, `TheoryNotFoundError`/`InvalidTheoryName`, `normalize_theory_name()`, `with_theory(**options)`, the `__main__` harness, the placeholder stage | `CR-2`, `TH-1`, `TH-2` | D-2, settled; placeholders not registered | **Done** |

Phase 1 is done and committed (`00d28fd`).

### Where logger-lab stands (review, 2026-10-22)

logger-lab is a **feedback system**, not only a debugging tool. Every record is
feedback for someone: a person at a terminal, whoever reads the files later, a
machine (JSON), or a live UI (relay subscribers). `Feedback_Guide.md` describes how
records travel.

- **Strong:** one composer (`lab()`) over four kinds of building block, with
  explicit composition rules. One handler per file across loggers. Thread-safe.
  Non-blocking `ASYNC` with tracebacks kept. Live subscribers. Rotation by size
  and time that never overwrites. JSON v1.2. 190 tests,
  pyrefly clean, concurrency tests shown to fail without their fix, verified
  on Windows and against LabFrame's real PySide6.
- **Gaps, in order of importance:**
  1. **No shared language for feedback.** Records travel, but "started / 40%
     / done / failed" has no standard shape, so LabFrame invents its own
     conventions.
  2. **No correlation:** nothing ties one job's or request's records together.
  3. **Delivery is fragile under misuse:** one slow output delays all async
     logging (`KN-19`), the queue is unbounded, and there's no rate limiting.
     (A subscriber feeding itself, `EX-7`, was fixed on 2026-10-23.)
  4. **One process only,** and configuration is code-only.
  5. **Not shipped:** 0.2.0 exists only on `release/v0.2.0`; LabFrame must
     switch from `get_logger` before it can upgrade.
  6. ~~**Positioning**~~: `pyproject.toml` describes feedback since 2026-10-23,
     with the license, authors, URLs and classifiers.

### Phase 2: ship 0.2.0

| Step | Task | Why |
| --- | --- | --- |
| 2.1 | ~~Re-entry guard in `RelayHandler` (`EX-7`)~~ | **Done 2026-10-23:** an echo reaches files and consoles but no subscriber, with and without `ASYNC` |
| 2.2 | ~~Promote `TIMED_FILE`~~ | **Done 2026-10-22:** it became the `TIMED` feature, in the four-kinds redesign (D-21, D-26) |
| 2.3 | Positioning: the `pyproject` description and README tagline describe feedback | **`pyproject` done 2026-10-23** (with license, authors, URLs, classifiers). The README tagline is unchanged |
| 2.4 | Merge to `main`, publish 0.2.0 to PyPI | Consumers are still on 0.1.1 |
| 2.5 | LabFrame adopts the `gui` profile (§5) | Required: 0.2.0 removes the `get_logger` call it uses |

### Phase 3: the feedback layer (the theory pipeline)

Ranked by value against cost (owner-approved ranking, 2026-10-22, D-20).
Ranks 1 and 2 go together: they turn logger-lab from "where logs go" into
"feedback".

| Rank | Theory | What it gives | Why this position | Depends on |
| --- | --- | --- | --- | --- |
| 1 | **`TRACE`** | A `job_id` / `trace_id` on every record, from `contextvars` | Ties feedback to a job or request, and answers LabFrame's correlation-ID note. **Constraint (measured):** context must be stamped on the **caller's** thread (a logger-level filter, or while `AsyncHandler` freezes the record); a filter on an output runs on the dispatch worker and sees no context. New threads don't inherit `contextvars`, so job runners must copy the context in (`contextvars.copy_context().run`), which LabFrame's `JobManager.submit` could do. | nothing |
| 2 | **`LIFECYCLE`** *(new)* | A standard shape for feedback events (`started`, `progress` with a fraction, `succeeded`, `failed`, `cleared`) and a helper on top of `log_event` | Lets subscribers drive a UI from records alone. LabFrame's channels could react to these events instead of their own level conventions. A console output could draw a Rich progress bar from them. | `TRACE` (for the job ID) |
| 3 | **`THROTTLE`** *(new)* | Coalescing and rate limits per subscriber ("…repeated 120×", records per second), as a feature on `relay` | Stops a tight error loop flooding a GUI (LabFrame note), and eases `KN-19`: fewer, larger batches hold the one worker for less time. | `relay` |
| 4 | **`PERFORMANCE`** | `@timed` durations, emitted as lifecycle events | Small, very visible, and plugs into ranks 1–2 | `TRACE`, `LIFECYCLE` |
| 5 | **`PROCESS`** *(new)* | Several processes, one log file: a single writer process owns the files | multiprocessing pools and several app instances. Bigger: records cross the process boundary pickled, with message and traceback already turned into text. A catalyst in the `dispatch` group, next to `ASYNC`. | the dispatch queue |
| 6 | **`HTTP`** | Request context (method, path, status, latency) on records | Specialized to web services | `TRACE` |
| 7 | **`SEC`** | A tamper-evident, append-only audit stream (hash-chained lines) | Valuable, but needs a real design (keys, a verification tool) | the shared file handlers |
| 8 | **`DB`** | Query logging with redaction (SQLAlchemy hooks) | A heavy dependency, so it must be an optional extra | D-5 |

`ASYNC` was promoted in 0.2.0 (with `relay`, for the `gui` profile), and is
now the first catalyst. The stdlib `QueueHandler`/`QueueListener` were
rejected: `prepare()` strips tracebacks, and each listener needs its own
thread. `TIMED_FILE` was promoted to the `TIMED` feature.

A theory can be any of the four kinds, or a helper. Each idea file names its
likely kind, and `theories/__init__.py` lists them. `THROTTLE` is likely a
feature of `relay`, `PROCESS` a `dispatch` catalyst, and `SEC` an output.
`TRACE` and `HTTP` stay open: their stamp must be taken on the caller's thread,
which a feature on an output can't do. `LIFECYCLE`, `PERFORMANCE` and `DB` are
helpers (Standards §3.4).

**Promotion rule (theory → building block):** the checklist in Standards
§3.4. Promoting means three steps. Give it a member of its kind's enum, move
the file into its kind's package, and add its spec to that kind's table in
`core/registry.py`. A helper is promoted into the public API instead.

### Phase 4: after the feedback layer

- Configuration from env or a dict (`lab().from_env()` / `from_dict()`).
- An exception helper (`@lab_catch(logger)`).
- An optional parent-logger mode (CR-9 option B).
- A capped async queue with a drop count, if a flood shows up (D-14).

---

## 4. Decisions

| ID | Decision | Status |
| --- | --- | --- |
| D-1 | File args are one shared set, forwarded to every factory | **Superseded by D-25 (2026-10-22):** options live on the building blocks. |
| D-2 | How theory-specific args reach a theory | **Locked in 2026-10-22:** `with_theory(theory, on=None, **options)`, merged over the theory spec's declared options (D-25). |
| D-3 | How `conspiracy_theorist` avoids two handlers on one file | **Locked in 2026-10-22.** Drop `file` from the profile, since `rotating_file` is `file` plus rotation. More generally, experiments never clash, and two handlers never share a file (Standards §2.3). |
| D-4 | Should `get_logger()` accept file args? | **Moot (2026-10-22):** `get_logger()` was removed (D-19). |
| D-5 | Optional dependencies for heavy theories go behind `pip` extras | **Deferred** until the `DB` theory is built |
| D-6 | `with_file_args()` called twice replaces every arg | **Superseded by D-25:** `with_file_args()` is gone; repeated calls merge per key. |
| D-7 | What happens when experiments clash (Step 3) | **Superseded by D-23 (2026-10-22):** channels went with experiments; the composition rules replace them. |
| D-8 | `with_experiment()` no longer accepts `TheoryType` | **Locked in 2026-10-22:** theories go through `with_theory()` only (Standards §3.4). |
| D-9 | Thread safety | **Locked in and implemented 2026-10-22:** thread-safe by default (Standards §2.4). Every experiment and profile must be thread-safe; theories get leeway in trial but must be thread-safe to be promoted. Process safety is separate and opt-in (Phase 3). |
| D-10 | Per-module levels and experiments | **Locked in and implemented 2026-10-22:** each module composes its own logger at its own level. Loggers on one file share one handler (option A, Standards §2.5). Option B (one parent logger that modules propagate to) stays a possible opt-in mode for later. |
| D-11 | Rules for loggers sharing a file | **Locked in 2026-10-22 (owner):** a different experiment on an open file → `LogFileClashError`; same experiment, different settings → first wins + `SharedFileSettingsWarning`; shared file handlers have no level (`NOTSET`); the file closes when its last logger releases it. logger-lab closes only handlers it created. |
| D-12 | `TIMED_FILE` default rotation | **Carried into D-26 and D-27:** daily at midnight by default; `backup_count` (default 3) is how many backups are kept. |
| D-13 | When the `gui` profile ships | **Locked in 2026-10-22 (owner):** now, with `ASYNC` and `RELAY` promoted to experiments in the same release. |
| D-14 | Async queue size | **Locked in 2026-10-22 (owner):** unbounded, like the stdlib. A capped queue with a drop count can come later if a flood shows up. |
| D-15 | Subscriber API | **Locked in 2026-10-22 (owner):** `with_subscriber(callback, level=None)`, which brings `relay` with it. Callbacks get the `LogRecord`, read-only. |
| D-16 | Where GUI logs go | **Locked in 2026-10-22 (owner):** left to the app via `.with_output("file", log_dir=...)`; no per-user default in logger-lab. |
| D-17 | Version for the async/relay/`gui`/`TIMED_FILE` work | **Locked in 2026-10-22 (owner):** it stays **0.2.0** (unpublished), not 0.3.0. |
| D-18 | Default level | **Superseded by D-22 (2026-10-22, owner).** |
| D-19 | Is `get_logger()` still needed, or is `lab()` the one composer? | **Locked in 2026-10-22 (owner):** `lab()` is the only composer; `get_logger()` is removed in 0.2.0. |
| D-20 | Roadmap and theory ranking | **Locked in 2026-10-22 (owner):** ship 0.2.0 first (Phase 2), then `TRACE` → `LIFECYCLE` → `THROTTLE` → `PERFORMANCE` → `PROCESS` → `HTTP` → `SEC` → `DB` (Phase 3). `LIFECYCLE`, `THROTTLE` and `PROCESS` added as placeholder theories. |
| D-21 | How a logger is composed | **Locked in 2026-10-22 (owner):** four kinds, each with its own method: `with_output()`, `with_feature()`, `with_format()`, `with_catalyst()` ("catalyst" over "pipeline"). One Rich console output; `MINIMAL` and `VERBOSE` are detail features for console and file (default detail: time + level + message). Formats `RICH`, `TEXT`, `JSON` are the fourth kind. All four kinds are available, and theories can be any of them. |
| D-22 | Default level | **Locked in 2026-10-22 (owner):** **INFO**, for every logger, observer included; levels are changed intentionally. The WARNING default is removed. |
| D-23 | Composition rules | **Locked in 2026-10-22 (owner):** no implicit outputs, so a feature never brings one; `on=` targets an output; one detail feature and one format per output, only where they work; one profile per builder; one catalyst per group. Anything that can actually break is a `CompositionError`. |
| D-24 | Hand-composing a profile | **Locked in 2026-10-22 (owner):** warn `ProfileSuggestionWarning` (e.g. console + file → `investigator`), only when following it adds nothing that wasn't asked for, naming the most specific profile. Refined 2026-10-23 (owner): the suggestion is replayed on the profile first and must plan the same, so it also never leads to a clash (`CR-12`). |
| D-25 | Where options go | **Locked in 2026-10-22 (owner):** on the building-block methods. `with_output("file", log_dir=...)` adds the output or configures it if it already exists (from a profile); repeated calls merge per key; unknown options are errors. `max_bytes` belongs to `ROTATING`; `backup_count` stays a file option; the console's `stream` defaults to stderr. `with_file_args()` is removed. |
| D-26 | `TIMED` | **Locked in 2026-10-22 (owner):** a full feature, with `at=` and `utc`. Its options were reshaped by D-27. With `ROTATING`, backups are named date + counter (`app.log.2026-10-22.1`); no backup is ever overwritten. |
| D-27 | `TIMED` options | **Locked in 2026-10-23 (owner):** the options of the `schedule` package, as keyword arguments: `every=` (a number), `unit=` (minute, hour, day, week, month; plurals too), `day=` (which makes it weekly), `at=` (`":MM"` for an hour, `"HH:MM"` otherwise) and `utc`. Weekdays are no longer values of `every`. `every` defaults to 1, so a unit alone means one of it. `unit=` and `day=` take the `Unit` and `Day` enums or their names (owner, 2026-10-23: `weekday=` was renamed `day=`). Unlike `schedule`, periods are anchored to the calendar and there is a `month` unit. `to=`, `until=`, seconds and timezone names are left out. |

---

## 5. Carried over from LabFrame's logger-lab notes

| LabFrame note | Where it lands here |
| --- | --- |
| No Qt-aware handler | **Done in 0.2.0:** `relay` + `with_subscriber()`. Pass a Qt signal's `emit`; logger-lab stays Qt-free. |
| `standard`/`investigator` write to stdout, which disappears in windowed builds | **Done in 0.2.0:** the `gui` profile has no console. |
| Feedback logging writes to disk on the GUI thread | **Done in 0.2.0:** `async` (inside `gui`). |
| No correlation-id convention | `TRACE` (Phase 3, rank 1) |
| No coalescing or rate limiting for GUI-facing handlers | `THROTTLE` (Phase 3, rank 3) |

**LabFrame adoption.** This is a LabFrame-side change, made once 0.2.0 is
published. It is required, because 0.2.0 removes the `get_logger()` call that
LabFrame uses today. In `LabFrame/feedback/channel.py`, delete `QtRelayHandler`,
keep `FeedbackLogRelay`, and build the feedback logger with:

```python
feedback_logger = (
    lab().with_profile("gui")
    .with_subscriber(feedback_log_relay.record_logged.emit)
    .with_output("file", log_dir=app_log_dir)   # a writable per-user directory
    .with_level("DEBUG")                   # LabFrame's channels log at DEBUG
    .build("LabFrame.feedback")
)
```

**Levels:** LabFrame's channels log in-progress and cleared states at DEBUG. With
the INFO default (D-22), those are dropped unless LabFrame sets the level:
`.with_level("DEBUG")` here.
Verified in LabFrame's environment: with no level, its DEBUG lines are not
written; INFO lines are.

The child channel loggers (`LabFrame.feedback.<Channel>`) need no change. Raise
LabFrame's pin to `logger-lab>=0.2.0`. Consider building the logger on first use
rather than at import (today it runs when `LabFrame.feedback` is imported).

---

## 6. Next immediate action

1. The owner commits 0.2.0 after round 1 of the cleanliness passes. The same
   commit untracks `.idea/` (`PK-13`).
2. Phase 2: merge to `main` and publish 0.2.0 (only when the owner says so),
   then LabFrame adoption (§5).
3. Phase 3, starting with `TRACE` + `LIFECYCLE` together.
4. When Project A, LabFrame and Anime-Earth upgrade from 0.1.1, they follow
   the migration table (§2). Project A's ~34 module loggers (`ROTATING_FILE`
   on `logs/app.log`) become `.with_output("file").with_feature("ROTATING")`
   and will share one handler, which fixes their Windows rotation. An app
   mixing a plain and a rotating file on one path will now raise
   `LogFileClashError` and needs its own `filename`.
