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
  `get_logger("LabFrame.feedback", experiment=ExperimentType.ROTATING_FILE)`).
  LabFrame's Standards doc keeps a list of logger-lab gaps found while
  integrating it; they are tracked here in §5.

---

## 2. Built (the stable core)

| Area | Status | Notes |
| --- | --- | --- |
| Experiments: `standard`, `verbose`, `minimalist`, `file`, `rotating_file`, `ai` | **Done** | All follow `(level, **kwargs) -> list[Handler]`. |
| Profiles: `observer`, `investigator`, `conspiracy_theorist`, `ai_agent` | **Done** | Each declares an `*_EXPERIMENTS` tuple, checked for clashes at registration. |
| Registry, with validated registration and typed lookup errors | **Done** | Experiments, profiles and theories; channels; profile compositions. |
| `LabBuilder` / `lab()` / `get_logger()` | **Done** | `plan()` enforces one experiment per channel; duplicates warn. |
| `JSONFormatter` + `log_event()`, Mosquito Lab Logging Standard v1 | **Done** | `log_event()` now attributes records to its caller (`KN-10`, fixed 2026-10-22). |
| Error hierarchy (`LabError` …) | **Done** | Adds `ExperimentClashError`, `TheoryNotFoundError`, `InvalidTheoryName` and `DuplicateExperimentWarning`. `InvalidLevelError` is still never raised (`KN-2`). |
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
| `with_experiment(TheoryType.X)` no longer accepted | **Yes** | Use `with_theory(...)` or `get_logger(theory=...)`. |
| Two different experiments on one channel raise `ExperimentClashError` (e.g. `standard` + `minimalist`, or `investigator` + `ROTATING`) | **Yes** | Keep one per channel. |
| A file already open as another experiment raises `LogFileClashError` (`FILE` vs `ROTATING` on one path, across loggers) | **Yes** | Give one of them its own `with_file_args(filename=...)`. |
| `conspiracy_theorist` is `verbose` + `rotating_file` (no plain `file`) | Behaviour | Nothing; records are no longer written twice. |
| File handlers are shared per path, have level `NOTSET`, and are `SharedFileHandler`/`SharedRotatingFileHandler` (still `FileHandler` subclasses) | Behaviour | Code checking `type(h) is FileHandler` should use `isinstance`. A logger's level does the filtering. |
| `clear_handlers()` releases handlers (shared files stay open while used) and never closes handlers logger-lab didn't create | Behaviour | Nothing. |
| `log_event()` records the caller as `source` | Fix | Nothing. |
| Duplicates warn (`DuplicateExperimentWarning`) and keep the first; a shared file with different settings warns (`SharedFileSettingsWarning`) | New | Optionally make the warnings errors in CI. |
| `with_file_args()`, `with_theory(**options)`, `plan()`; theory string names; `register_theory()`; `Channel`; new errors; `py.typed` | New | — |
| Thread-safe by default (Standards §2.4) | New | — |

`with_log_dir()` existed only between releases (it was never published), so
its replacement by `with_file_args()` isn't a breaking change for consumers.

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

Ranked by value against cost. The first three also close gaps LabFrame has
already reported (§5).

| Rank | Theory | Mechanism | Why this position | Depends on |
| --- | --- | --- | --- | --- |
| 1 | **`TIMED_FILE`** | `TimedRotatingFileHandler` | Already registered, smallest step, reuses `get_log_dir()` and the file args. A good test of the theory → experiment promotion path. | Needs `when`/`interval`/`utc` (D-2) |
| 2 | **`TRACE`** | `logging.Filter` + `contextvars` that inject `trace_id`/`span_id` | Answers LabFrame's "no correlation-id convention" note (`job_id`). Fits straight into `JSONFormatter`'s `extra`. Pure stdlib. | None |
| 3 | **`ASYNC`** | `QueueHandler` + `QueueListener` | Non-blocking dispatch for asyncio and threads. This is also the right base for LabFrame's Qt-relay and rate-limit asks, which then become thin handlers on top. Needs a shutdown story (`listener.stop()` via `atexit`). | None |
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

- **GUI profile** (LabFrame's ask): rotating file + Qt/queue relay, with no
  stdout and no Rich. That suits `pythonw` and windowed PyInstaller builds,
  where stdout disappears.
- **Strict mode**: an opt-in `with_level(..., strict=True)` that raises
  `InvalidLevelError` (`KN-2`).
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
| D-9 | Thread safety | **Locked in and implemented 2026-10-22:** thread-safe by default (Standards §2.4). Every experiment and profile must be thread-safe; theories get leeway in trial but must be thread-safe to be promoted. Process safety is separate and opt-in (the `ASYNC` theory). |
| D-10 | Per-module levels and experiments | **Locked in and implemented 2026-10-22:** each module composes its own logger at its own level. Loggers on one file share one handler (option A, Standards §2.5). Option B (one parent logger that modules propagate to) stays a possible opt-in mode for later. |
| D-11 | Rules for loggers sharing a file | **Locked in 2026-10-22 (owner):** a different experiment on an open file → `LogFileClashError`; same experiment, different settings → first wins + `SharedFileSettingsWarning`; shared file handlers have no level (`NOTSET`); the file closes when its last logger releases it. logger-lab closes only handlers it created. |
| D-8 | `with_experiment()` no longer accepts `TheoryType` | **Locked in 2026-10-22:** theories go through `with_theory()` only (Standards §3.4). |
| D-4 | Should `get_logger()` accept file args? | **Open.** Recommendation: no, keep it a one-liner and point to `lab()` |
| D-5 | Optional dependencies for heavy theories go behind `pip` extras | **Proposed** |
| D-6 | `with_file_args()` called twice replaces every arg, not just the ones passed | **Locked in** (documented in the docstring) |

---

## 5. Carried over from LabFrame's logger-lab notes

| LabFrame note | Where it lands here |
| --- | --- |
| No Qt-aware handler | Phase 3 GUI profile, built on the `ASYNC` queue (Phase 2, rank 3). LabFrame has its own relay in the meantime, so this is not blocking. |
| `standard`/`investigator` write to stdout, which disappears in windowed builds | Phase 3 GUI profile |
| No correlation-id convention | `TRACE` (Phase 2, rank 2) |
| No coalescing or rate limiting for GUI-facing handlers | A filter or wrapper on top of `ASYNC`, scoped to the GUI profile |

---

## 6. Next immediate action

1. The owner reviews the code preview (Phase 1, `KN-10`, the test guard, and
   shared, thread-safe file handling) and says whether to commit.
2. Start cleanliness pass 1 (`logging_kernel`).
3. When Project A, LabFrame and Anime-Earth upgrade from 0.1.1: Project A's
   ~34 module loggers (`ROTATING_FILE` on `logs/app.log`) will share one
   handler, which fixes their Windows rotation. LabFrame's feedback logger
   (also `ROTATING_FILE`, default path) shares cleanly. An app mixing `FILE`
   and `ROTATING` on one path will now raise `LogFileClashError` and needs its
   own `filename`.
