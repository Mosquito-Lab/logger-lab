# Continuation Doc — logger-lab

**Purpose:** self-contained context for continuing logger-lab in a fresh
conversation. Read it cold and pick up from "Next immediate action" at the
bottom. This doc owns the roadmap, the theory pipeline, locked-in decisions,
and what is built and what isn't. The rules live in `Standards_and_Tracker.md`.
Every finding ID used here (`PF-1`, `KN-1` and so on) is defined in
`Cleanliness_Tracker.md`.

**Last updated:** 2026-10-22

---

## 1. Where logger-lab sits

- **logger-lab** (`v0.2.0`, Python ≥ 3.10, only dependency `rich`): a
  composable layer over stdlib `logging`, built as experiments → profiles →
  builder. See the API Reference.
- **LabFrame**: the PySide6 framework, and logger-lab's first real consumer
  (`LabFrame.feedback.channel` calls
  `get_logger("LabFrame.feedback", experiment=ExperimentType.ROTATING_FILE)`,
  which 0.2.0 removes — see the LabFrame adoption step in §5).
  LabFrame's Standards doc keeps a list of logger-lab gaps found while
  integrating it; they are tracked here in §5.

---

## 2. Built (the stable core)

| Area | Status | Notes |
| --- | --- | --- |
| Experiments: `standard`, `verbose`, `minimalist`, `file`, `rotating_file`, `ai` | **Done** | All follow `(level, **kwargs) -> list[Handler]`. |
| Profiles: `observer`, `investigator`, `conspiracy_theorist`, `ai_agent` | **Done** | Each declares an `*_EXPERIMENTS` tuple, checked for clashes at registration. |
| Registry, with validated registration and typed lookup errors | **Done** | Experiments, profiles and theories; channels; profile compositions. |
| `LabBuilder` / `lab()` | **Done** | The only composer (`get_logger()` removed, D-19). `plan()` enforces one experiment per channel; duplicates warn. |
| `JSONFormatter` + `log_event()`, Mosquito Lab Logging Standard v1.1 | **Done** | v1.1 adds `logger`, `exception` and `stack` (`KN-11`, `KN-17`); `log_event()` attributes records to its caller (`KN-10`). |
| Error hierarchy (`LabError` …) | **Done** | Adds `ExperimentClashError`, `TheoryNotFoundError`, `InvalidTheoryName` and `DuplicateExperimentWarning`. `InvalidLevelError` is raised for invalid levels (`KN-2`). |
| Name resolution (enum member or value string) | **Done** | Experiments, profiles and theories, case-insensitive; pinned by `tests/test_names.py`. |
| Tests + type check | **Done** | 112 tests (including concurrency); pyrefly clean. |
| One file, one handler across loggers; thread safety | **Done 2026-10-22** | `share_file_handler()`, atomic `install_handlers()`, stay-closed file handlers (`CR-9`, `CR-10`, `TS-4`). |
| British-to-American spelling pass (`normalisers` → `normalizers`, etc.) | **Done, 2026-10-22** | Shipped in 0.2.0. |

### 0.2.0 changes (2026-10-22)

The public changes since 0.1.1 (Standards §3.3). **Breaking** items need
consumer action.

| Change | Breaking? | What a consumer does |
| --- | --- | --- |
| `logging_kernel.normalisers` renamed to `normalizers` (`normalise_*` → `normalize_*`) | **Yes** | Update the import. The top-level `logger_lab` API is unchanged. |
| `with_experiment(TheoryType.X)` no longer accepted | **Yes** | Use `with_theory(...)`. |
| Two different experiments on one channel raise `ExperimentClashError` (e.g. `standard` + `minimalist`, or `investigator` + `ROTATING`) | **Yes** | Keep one per channel. |
| A file already open as another experiment raises `LogFileClashError` (`FILE` vs `ROTATING` on one path, across loggers) | **Yes** | Give one of them its own `with_file_args(filename=...)`. |
| `conspiracy_theorist` is `verbose` + `rotating_file` (no plain `file`) | Behaviour | Nothing; records are no longer written twice. |
| File handlers are shared per path, have level `NOTSET`, and are `SharedFileHandler`/`SharedRotatingFileHandler` (still `FileHandler` subclasses) | Behaviour | Code checking `type(h) is FileHandler` should use `isinstance`. A logger's level does the filtering. |
| `clear_handlers()` releases handlers (shared files stay open while used) and never closes handlers logger-lab didn't create | Behaviour | Nothing. |
| `log_event()` records the caller as `source` | Fix | Nothing. |
| Duplicates warn (`DuplicateExperimentWarning`) and keep the first; a shared file with different settings warns (`SharedFileSettingsWarning`) | New | Optionally make the warnings errors in CI. |
| `with_file_args()`, `with_theory(**options)`, `plan()`; theory string names; `register_theory()`; `Channel`; new errors; `py.typed` | New | — |
| Thread-safe by default (Standards §2.4) | New | — |
| `TheoryType.ASYNC` removed (promoted to `ExperimentType.ASYNC`) | **Yes** (theory API; theories are unstable) | Use `with_experiment("ASYNC")`. |
| `TIMED_FILE` theory registered (trial): selecting it builds a logger instead of raising `TheoryNotFoundError` | Behaviour | — |
| `async` experiment (`DISPATCH` channel) and `drain()` | New | Add `.with_experiment("ASYNC")` to move writing off the calling thread. |
| `relay` experiment (`LIVE` channel) and `with_subscriber(callback, level=None)` | New | Replace a hand-written callback/Qt handler with a subscriber. |
| `gui` profile: `rotating_file` + `relay` + `async`, no console | New | LabFrame: see §5. |
| `Channel.LIVE`, `Channel.DISPATCH`; the `@dispatcher` marker; `install_handlers(..., dispatcher=)`; `BuilderError(reason=)` | New | — |
| **`get_logger()` removed** — `lab()` is the only composer (D-19) | **Yes** | `get_logger(name, profile="investigator", level="DEBUG")` → `lab().with_profile("investigator").with_level("DEBUG").build(name)`. Likewise `experiment=` → `.with_experiment(...)`, `theory=` → `.with_theory(...)`. |
| Invalid levels raise `InvalidLevelError` (a typo like `"DEBG"` used to become INFO silently) | **Yes** | Fix the level name. |
| One default level: **INFO**, **WARNING** when `minimalist` is in the logger. `lab()` + `observer` used to be INFO | **Yes** | Call `with_level()` if you relied on another level. **LabFrame:** its DEBUG feedback lines need `level="DEBUG"` (§5). |
| `build_console_formatter()` removed | **Yes** | Use `logging.Formatter("%(message)s")`. |
| `profiles._base._build_profile` → public `profiles.base.build_profile` (exported from `logger_lab.profiles`) | **Yes** | Update the import. |
| JSON: Mosquito Lab Standard **v1.1** adds `logger`, `exception{type,message,traceback}` and `stack` | New | — (v1 fields unchanged) |
| `main.py` and `src/__init__.py` deleted; docs moved to a repo-root `docs/` (no longer in the wheel) | Packaging | — |

`with_log_dir()` existed only between releases (it was never published), so
its replacement by `with_file_args()` isn't a breaking change for consumers.

The async, relay, `gui` and `TIMED_FILE` work landed after commit `3adfa9c`,
still as 0.2.0 (owner, 2026-10-22). Verified: 181 tests (the concurrency tests
five runs in a row, each shown to fail when its guarantee is broken), pyrefly
clean, and an integration check in LabFrame's own environment with real
PySide6:
1. LabFrame's **current** `channel.py` works unchanged on 0.2.0.
2. With the `gui` profile, records logged on a worker thread and on the GUI
   thread both reached a Qt slot **on the GUI thread**, and the file.

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
| 0 | Test and type-check baseline: `uv_build`, a `dev` group (pytest, pyrefly), `tests/`, `py.typed`, root `.gitignore` | `PK-3`, `TS-1`, `PK-6` | — | **Done 2026-10-22**: 97 passed, pyrefly 0 errors |
| 1 | `conspiracy_theorist` becomes `verbose` + `rotating_file` only | `PF-1`, `EX-5` | — | **Done**: rotation verified on Windows |
| 2 | `clear_handlers()` closes the handlers it detaches | `KN-1` | — | **Done**. The builder no longer hands handlers over from the profile, so nothing moved gets closed. |
| 3 | One experiment per channel (console, file, JSON); clash → `ExperimentClashError`; duplicate → `DuplicateExperimentWarning`, first kept | `CR-1` (+ `CR-8` as a side effect) | D-7, settled | **Done**. Two *loggers* sharing a file stays open as `CR-9`. |
| 4 | Enum and value names pinned for every member; README and docs corrected | `DOC-1` | Case-insensitive: kept | **Done** |
| 5 | Theory rework: `register_theory()`, `TheoryNotFoundError`/`InvalidTheoryName`, `normalize_theory_name()`, `with_theory(**options)`, the `__main__` harness, the placeholder stage | `CR-2`, `TH-1`, `TH-2` | D-2, settled; placeholders not registered | **Done** |

**Awaiting:** the owner's review of the code preview, and the go-ahead to
commit.

The remaining findings (`KN-*`, `CR-3`…`CR-8`, `EX-*`, `PF-2/3`, `TH-3`, `PK-*`)
are handled in the cleanliness passes after Phase 1.

### Phase 2: the theory pipeline

Ranked by value against cost.

| Rank | Theory | Mechanism | Status / why this position | Depends on |
| --- | --- | --- | --- | --- |
| 1 | **`TIMED_FILE`** | `TimedRotatingFileHandler`, shared via `share_file_handler()` | **Trial since 0.2.0.** Registered, tested (defaults, options, forced rollover, sharing, clashes, behind `async`). To promote: a concurrency test, a pass row, an `ExperimentType` value. | — |
| 2 | **`TRACE`** | `logging.Filter` + `contextvars` that inject `trace_id`/`span_id` | Next. Answers LabFrame's "no correlation-id convention" note (`job_id`). Fits straight into `JSONFormatter`'s `extra`. Pure stdlib. | None |
| ✔ | **`ASYNC`** | Own queue + one worker (`logging_kernel.dispatch`) | **Promoted to an experiment in 0.2.0** (with `relay`, for the `gui` profile). The stdlib `QueueHandler`/`QueueListener` were rejected: `prepare()` strips tracebacks, and each listener needs its own thread. | — |
| 4 | **`PERFORMANCE`** | `@timed` decorator that emits duration through `log_event` | Small and very visible. Builds on `TRACE` context if it exists. | `TRACE` (optional) |
| 5 | **`HTTP`** | Filter that injects method, path, status and latency from request context | Useful, but it depends on the framework. Use `contextvars` (from `TRACE`), not thread-locals. | `TRACE` |
| 6 | **`SEC`** | Separate append-only audit stream that is tamper-evident (hash-chained lines) | Valuable but needs a real design (key handling, verification tool). | `TIMED_FILE` / file args |
| 7 | **`DB`** | SQLAlchemy event hooks + redaction filter | Adds a heavy dependency, so it must be an optional extra (`logger-lab[db]`). Do it last. | Optional-deps policy (D-5) |

**Promotion rule (theory → experiment):** a theory is promoted once it has
(a) the standard signature including `**kwargs`, (b) tests, (c) docstrings to
the standard, and (d) a row in the API Reference. Promoting it means adding an
`ExperimentType` value, moving the file to `experiments/` and adding it to the
registration loop.

### Phase 3: new profiles and polish

- ~~**GUI profile**~~: shipped in 0.2.0 (`rotating_file` + `relay` + `async`).
- **Process safety**: several processes writing one file, built on the
  dispatch queue (one writer process).
- **Rate limiting for GUI subscribers**: a relay option that coalesces floods
  (LabFrame note).
- Comparison-driven features (see the Framework Comparison doc): env/dict
  configuration, `exception`/`catch` helpers, redaction filters.

---

## 4. Decisions

| ID | Decision | Status |
| --- | --- | --- |
| D-1 | File args are one shared set, forwarded to every factory; factories ignore what they don't use | **Locked in, implemented 2026-10-22** |
| D-2 | How theory-specific args (for example `TimedRotatingFileHandler`'s `when`/`interval`) reach a factory | **Locked in 2026-10-22:** `with_theory(theory, **options)`. The options go to that theory only, on top of the file args. |
| D-3 | How `conspiracy_theorist` avoids two handlers on one file | **Locked in 2026-10-22.** Drop `file` from the profile, since `rotating_file` is `file` plus rotation. More generally, experiments never clash, and two handlers never share a file (Standards §2.3). |
| D-7 | What happens when experiments clash (Step 3) | **Locked in 2026-10-22:** at most one experiment per channel (console, file, JSON). Two different experiments on one channel raise `ExperimentClashError`, explaining the rule. The same experiment twice warns and keeps the first. The scope is one logger. |
| D-9 | Thread safety | **Locked in and implemented 2026-10-22:** thread-safe by default (Standards §2.4). Every experiment and profile must be thread-safe; theories get leeway in trial but must be thread-safe to be promoted. Process safety is separate and opt-in (Phase 3). |
| D-10 | Per-module levels and experiments | **Locked in and implemented 2026-10-22:** each module composes its own logger at its own level. Loggers on one file share one handler (option A, Standards §2.5). Option B (one parent logger that modules propagate to) stays a possible opt-in mode for later. |
| D-11 | Rules for loggers sharing a file | **Locked in 2026-10-22 (owner):** a different experiment on an open file → `LogFileClashError`; same experiment, different settings → first wins + `SharedFileSettingsWarning`; shared file handlers have no level (`NOTSET`); the file closes when its last logger releases it. logger-lab closes only handlers it created. |
| D-8 | `with_experiment()` no longer accepts `TheoryType` | **Locked in 2026-10-22:** theories go through `with_theory()` only (Standards §3.4). |
| D-12 | `TIMED_FILE` default rotation | **Locked in 2026-10-22 (owner):** `when="midnight"`, one file a day; `backup_count` (default 3) is the number of days kept. |
| D-13 | When the `gui` profile ships | **Locked in 2026-10-22 (owner):** now, with `ASYNC` and `RELAY` promoted to experiments in the same release. |
| D-18 | Default level | **Locked in 2026-10-22 (owner):** INFO, and WARNING for `observer` and `minimalist` (any logger that includes `minimalist`). Invalid levels raise. |
| D-19 | Is `get_logger()` still needed, or is `lab()` the one composer? | **Locked in 2026-10-22 (owner):** `lab()` is the only composer; `get_logger()` is removed in 0.2.0. |
| D-17 | Version for the async/relay/`gui`/`TIMED_FILE` work | **Locked in 2026-10-22 (owner):** it stays **0.2.0** (unpublished), not 0.2.0. |
| D-14 | Async queue size | **Locked in 2026-10-22 (owner):** unbounded, like the stdlib. A capped queue with a drop count can come later if a flood shows up. |
| D-15 | Subscriber API | **Locked in 2026-10-22 (owner):** `with_subscriber(callback, level=None)`, which brings `relay` with it. Callbacks get the `LogRecord`, read-only. |
| D-16 | Where GUI logs go | **Locked in 2026-10-22 (owner):** left to the app via `with_file_args(log_dir=...)`; no per-user default in logger-lab. |
| D-4 | Should `get_logger()` accept file args? | **Moot (2026-10-22):** `get_logger()` was removed (D-19). |
| D-5 | Optional dependencies for heavy theories go behind `pip` extras | **Deferred** until the `DB` theory is built |
| D-6 | `with_file_args()` called twice replaces every arg, not just the ones passed | **Locked in** (documented in the docstring) |

---

## 5. Carried over from LabFrame's logger-lab notes

| LabFrame note | Where it lands here |
| --- | --- |
| No Qt-aware handler | **Done in 0.2.0:** `relay` + `with_subscriber()`. Pass a Qt signal's `emit`; logger-lab stays Qt-free. |
| `standard`/`investigator` write to stdout, which disappears in windowed builds | **Done in 0.2.0:** the `gui` profile has no console. |
| Feedback logging writes to disk on the GUI thread | **Done in 0.2.0:** `async` (inside `gui`). |
| No correlation-id convention | `TRACE` (Phase 2, rank 2) |
| No coalescing or rate limiting for GUI-facing handlers | Phase 3, a relay option |

**LabFrame adoption (a LabFrame-side change, once 0.2.0 is published, and
required: 0.2.0 removes the `get_logger()` call LabFrame uses today):** in
`LabFrame/feedback/channel.py`, delete `QtRelayHandler`, keep
`FeedbackLogRelay`, and build the feedback logger with:

```python
feedback_logger = (
    lab().with_profile("gui")
    .with_subscriber(feedback_log_relay.record_logged.emit)
    .with_file_args(log_dir=app_log_dir)   # a writable per-user directory
    .with_level("DEBUG")                   # LabFrame's channels log at DEBUG
    .build("LabFrame.feedback")
)
```

**Levels:** LabFrame's channels log in-progress and cleared states at DEBUG. With
the INFO default (D-18), those are dropped unless LabFrame sets the level:
`.with_level("DEBUG")` here.
Verified in LabFrame's environment: with no level, its DEBUG lines are not
written; INFO lines are.

The child channel loggers (`LabFrame.feedback.<Channel>`) need no change. Raise
LabFrame's pin to `logger-lab>=0.2.0`. Consider building the logger on first use
rather than at import (today it runs when `LabFrame.feedback` is imported).

---

## 6. Next immediate action

1. The owner reviews the code preview (async, relay, `gui`, `TIMED_FILE`, and every flagged fix, all 0.2.0) and says whether to commit.
2. LabFrame adoption of the `gui` profile (§5), in the LabFrame repo.
3. `TIMED_FILE` promotion, then `TRACE`. Cleanliness passes resume when the
   owner says (paused 2026-10-22); every finding flagged so far is fixed.
4. When Project A, LabFrame and Anime-Earth upgrade from 0.1.1: Project A's
   ~34 module loggers (`ROTATING_FILE` on `logs/app.log`) will share one
   handler, which fixes their Windows rotation. LabFrame's feedback logger
   (also `ROTATING_FILE`, default path) shares cleanly. An app mixing `FILE`
   and `ROTATING` on one path will now raise `LogFileClashError` and needs its
   own `filename`.
