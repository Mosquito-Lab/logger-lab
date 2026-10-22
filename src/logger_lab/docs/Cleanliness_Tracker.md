# Cleanliness & Efficiency Tracker

This is the file-level review ledger for `logger_lab`. **Round 1 opened on
2026-10-22.** The ledger starts from the project-wide review that day. Phase 1
(Steps 0–5) closed its findings the same day; no file pass has run yet.

**Purpose:** one place to see four things:

- how clean, efficient and tested every package and file is
- which passes are done
- what was found and fixed
- what is still open

The rules being checked against are in `Standards_and_Tracker.md`.

---

## How a pass works

A **pass** reviews one package, one file at a time:

1. **Read and list.** I read the file in full, score it, and list its findings
   by type, each with an ID. Non-trivial fixes come with a before/after.
2. **Decide.** The owner approves which findings get fixed. Nothing is written
   before that.
3. **Fix and verify.** I apply the approved fixes, then run `uv run pytest -q`
   and `uv run pyrefly check` from the repository root. Until the baseline
   exists (`PK-3`, `TS-1`), verification is a script run with `PYTHONPATH=src`,
   recorded as such.
4. **Re-score.** I re-rate the file here, then move to the next file.
5. **Close.** After the last file, I review the package as a whole
   (structure, exports, duplication, layering) and close the package row.
   The owner commits.

Steps 1 to 5 in `Continuation.md` (the queued work) follow the same
propose → approve → fix → verify cycle, and their findings are closed here.

### The file checklist

| Check | Looks for |
|---|---|
| **Correctness** | Bugs and unhandled edge cases. Typed errors instead of bare `KeyError`/`TypeError`. No two handlers on one file. Behaviour on Windows (file locks). |
| **Truthful docs** | Docstrings, Args, Returns and Raises that match the code, with no stale names (`_configure_handler`, `*Factory`, `normalisers`). |
| **Dead code** | Unused imports, parameters, functions or constants; branches that can never run. |
| **Consistency** | `X \| None` typing, keyword arguments at call sites, American spelling, `_` prefixes only with a stated reason, `__all__` matching imports, module docstring, trailing newline, banners. |
| **Contracts** | Extension points follow the API standard (`**kwargs`, `configure_handler`, `get_log_dir`). Names resolve by member and by value. |
| **Simplicity** | Duplication, overlong functions, deep nesting, magic numbers that belong in `constants`. |
| **Efficiency** | Repeated work on the emit path. Setup work that is repeated per record. |
| **Tests** | The file's behaviour pinned by an offline test. |

**Layering rule:** imports point down only:
constants ← errors ← formatters/handlers ← enums ← normalizers ←
experiments/theories ← profiles ← registry ← builder ← `__init__`.
Each concern has one owner (`Standards_and_Tracker.md` §2).

### Scores

| Score | Clean | Eff |
|---|---|---|
| 9–10 | Truthful docs, consistent style and typing, no dead code, clear names | No redundant work on the emit path; setup work done once |
| 7–8 | Minor nits: spacing, comment fluff, stale wording | Small redundant work, tolerable |
| ≤6 | Docs that are wrong, dead checks, bad names, structural duplication | Real waste (per-record work that could be done once) |

**Tests:** ✓ behaviour covered · partial · none · n/a (nothing to test). Marked from the 0.2.0 suite; each pass re-checks its own files.
**Status:** `closed` = reviewed, fixed, re-rated · `in review` · `pending`.

**Finding IDs:** `KN-` logging_kernel · `CR-` core · `EX-` experiments ·
`PF-` profiles · `TH-` theories · `PK-` package root and packaging · `TS-`
tests · `DOC-` README and docs.

---

## Round 1 passes

| # | Pass | Files | LOC | Clean | Eff | Status |
|---|---|---:|---:|---:|---:|---|
| 1 | `logging_kernel` | 6 | 1,276 | — | — | pending |
| 2 | `core` | 4 | 855 | — | — | pending |
| 3 | `experiments` | 7 | 385 | — | — | pending |
| 4 | `profiles` | 6 | 231 | — | — | pending |
| 5 | `theories` | 9 | 74 | — | — | pending |
| 6 | Package root (`__init__.py`, `main.py`, `src/__init__.py`, `pyproject.toml`) | 3 + 1 | 181 | — | — | pending |
| 7 | `tests/` | 8 | 813 | — | — | created 2026-10-22, pending review |
| 8 | README + `docs/` | 6 | — | — | — | pending |
| — | **Total (Python, `src/`)** | **35** | **3,002** | | | 0 of 8 closed |

LOC recounted 2026-10-22 at 0.2.0, before any pass. (The first count, before Phase 1, was 2,123.)

---

## File-level detail

### 1. logging_kernel: pending

Order: `constants` → `errors` → `handlers` → `formatters` → `normalizers` →
`__init__`.

| File | LOC | Clean | Eff | Tests | Notes |
|---|---:|---:|---:|---|---|
| `constants.py` | 16 | — | — | n/a | Open: `KN-7` |
| `errors.py` | 499 | — | — | partial | Open: `KN-4`, `KN-9` |
| `handlers.py` | 339 | — | — | ✓ | Open: `KN-5`, `KN-7` · fixed: `KN-1`, `KN-12`, `CR-9`, `CR-10` |
| `formatters.py` | 152 | — | — | partial | Open: `KN-6`, `KN-7`, `KN-9`, `KN-11` · fixed: `KN-10` |
| `normalizers.py` | 166 | — | — | partial | Open: `KN-2`, `KN-3`, `KN-7`, `KN-8` |
| `__init__.py` | 104 | — | — | n/a | |

### 2. core: pending

| File | LOC | Clean | Eff | Tests | Notes |
|---|---:|---:|---:|---|---|
| `enums.py` | 41 | — | — | ✓ | Open: `CR-6` |
| `registry.py` | 436 | — | — | ✓ | Open: `CR-3`, `CR-4` · fixed: `CR-2`, `CR-5` |
| `builder.py` | 349 | — | — | ✓ | Open: `CR-7` · fixed: `CR-1`, `CR-2`, `CR-8`, `CR-10` |
| `__init__.py` | 29 | — | — | n/a | |

### 3. experiments: pending

| File | LOC | Clean | Eff | Tests | Notes |
|---|---:|---:|---:|---|---|
| `standard.py` | 48 | — | — | ✓ | Open: `EX-2` |
| `verbose.py` | 49 | — | — | ✓ | Open: `EX-3` |
| `minimalist.py` | 43 | — | — | ✓ | |
| `file.py` | 76 | — | — | ✓ | fixed: `EX-5`, `CR-9` |
| `rotating_file.py` | 101 | — | — | ✓ | fixed: `EX-1`, `CR-9` |
| `ai.py` | 53 | — | — | ✓ | |
| `__init__.py` | 15 | — | — | n/a | Open: `EX-4` |

### 4. profiles: pending

| File | LOC | Clean | Eff | Tests | Notes |
|---|---:|---:|---:|---|---|
| `_base.py` | 58 | — | — | ✓ | Open: `PF-2` · now installs atomically (`CR-10`) |
| `observer.py` | 36 | — | — | ✓ | |
| `investigator.py` | 39 | — | — | ✓ | |
| `conspiracy_theorist.py` | 39 | — | — | ✓ | fixed: `PF-1` |
| `ai_agent.py` | 46 | — | — | ✓ | |
| `__init__.py` | 13 | — | — | n/a | Open: `PF-2`, `PF-3` |

### 5. theories: pending

| File | LOC | Clean | Eff | Tests | Notes |
|---|---:|---:|---:|---|---|
| `timed_file_exp.py` | 29 | — | — | n/a | fixed: `TH-1` |
| `_test_theory.py` | 33 | — | — | n/a | fixed: `TH-2` |
| `async_exp.py`, `db_exp.py`, `http_exp.py`, `performance_exp.py`, `sec_exp.py`, `trace_exp.py` | 9 | — | — | n/a | Idea stage; has `TH-3` |
| `__init__.py` | 0 | — | — | n/a | Empty |

### 6. Package root: pending

| File | LOC | Clean | Eff | Tests | Notes |
|---|---:|---:|---:|---|---|
| `logger_lab/__init__.py` | 135 | — | — | ✓ | fixed: `PK-2` |
| `main.py` | 39 | — | — | n/a | Open: `PK-4` |
| `src/__init__.py` | 7 | — | — | n/a | Open: `PK-1` |
| `pyproject.toml` | — | — | — | n/a | fixed: `PK-3` |

### 7. tests: created 2026-10-22 (112 tests)

| File | Tests | Covers |
|---|---:|---|
| `conftest.py` | — | Each test runs in `tmp_path`; every handler is released afterwards; guards fail any test or run that logs to a file inside the repo (`TS-3`) or leaves the shared file table non-empty (a leak) |
| `test_names.py` | 56 | Member, value and lowercase for every experiment, profile and theory; renamed members rejected |
| `test_composition.py` | 14 | Channels, clashes, duplicates, untouched-on-error, conspiracy_theorist |
| `test_files.py` | 15 | Defaults, file args everywhere, rotating args, closing, Windows rotation |
| `test_registry.py` | 9 | Clashing or unregistered profile compositions, profile function = declaration, theory registration and options |
| `test_sharing.py` | 11 | One handler per file across loggers, per-module levels and experiments, clash, first-wins warning, sole-owner rebuild, last-release close, foreign handlers untouched, no reopen after close |
| `test_threads.py` | 3 | Concurrent builds, 8-thread rotation without losing a line, rebuilding mid-traffic |
| `test_formatters.py` | 4 | JSON v1 fields, `log_event` extra and caller source, non-serializable fallback |

Goal: pin the behaviour consumers depend on (Standards §4). Don't add tests
that only restate the obvious. A removed test is listed here with the reason.

### 8. README + docs: pending

| File | Notes |
|---|---|
| `README.md` | fixed: `DOC-1`, `PK-7` (updated for 0.2.0) |
| `docs/*.md` | Open: `PK-5` (ships in the wheel) · fixed: `DOC-2` · all five docs updated for 0.2.0 |

---

## Findings ledger (Round 1)

| ID | Type | File | Finding | Decision | Status |
|---|---|---|---|---|---|
| PF-1 | Bug | `profiles/conspiracy_theorist.py` | `file` and `rotating_file` both write to `app.log`. On Windows every rollover fails with `PermissionError [WinError 32]`, because `FileHandler` holds the file open (reproduced with `max_bytes=200`). Every record is also written to one path twice. | Profile becomes `verbose` + `rotating_file` only. `rotating_file` is `file` plus rotation (owner, 2026-10-22). **Done:** `test_conspiracy_theorist_rotates` rolls over on Windows with no `PermissionError` | fixed |
| KN-1 | Bug | `logging_kernel/handlers.py` | `clear_handlers()` detaches handlers without closing them. Rebuilding a logger name leaves the old file stream open (verified). | Close before detaching. The builder's profile hand-off must not close the handlers it moves. **Done:** closes before detaching; the builder no longer hands handlers over from the profile. `test_clear_handlers_closes_what_it_removes`, `test_rebuilding_…` | fixed |
| CR-1 | Bug | `core/builder.py` | Nothing stops two handlers sharing a file: a profile plus an experiment (`investigator` + `ROTATING`), the same experiment queued twice, or two loggers on the default `app.log` (all three verified). | At most one experiment per channel (console, file, JSON). A clash raises `ExperimentClashError`; a duplicate warns and keeps the first; the scope is one logger (owner, 2026-10-22). **Done:** `plan()` + `find_channel_clash()`; profile compositions checked at registration. `tests/test_composition.py`. The two-loggers case moved to `CR-9`. | fixed |
| CR-2 | Bug / Design | `core/registry.py`, `core/builder.py` | Theories: `get_theory()` prints and then raises `KeyError`; `THEORIES` is filled by hand with no validation; theories enter through `with_experiment()`'s `isinstance` branch; no string names (`"TIMED_FILE"` → `InvalidExperimentName`); no way to pass theory-specific options. | Rework per Standards §3.4. Open: options on `with_theory()` versus extending `with_file_args()` (D-2); register placeholders or not. **Done:** `register_theory()`, `TheoryNotFoundError`/`InvalidTheoryName`, `normalize_theory_name()`, `with_theory(**options)`; placeholders unregistered. `tests/test_registry.py`, `test_names.py` | fixed |
| TH-1 | Bug | `theories/timed_file_exp.py` | The registered placeholder returns `None`, so `build()` raises `TypeError: 'NoneType' object is not iterable`. | Part of Step 5 (placeholder stage, §3.4) **Done:** unregistered; the stub raises `NotImplementedError` and its docstring states the plan | fixed |
| TH-2 | Consistency | `theories/_test_theory.py` | Builds a logger as soon as it is imported. | Make it a `__main__` harness **Done:** `python -m logger_lab.theories._test_theory NAME`; run 2026-10-22 | fixed |
| DOC-1 | Doc | `README.md` | Says `rotating_file`, but the value is `"ROTATING"`, so `get_logger(experiment="rotating_file")` raises. Doesn't mention `with_file_args()`. The architecture tree says `normalisers.py` and `_configure_handler()`. British spellings remain. Profile table out of date after Step 1. | Rewrite the affected sections **Done:** README rewritten: values, channels, file args, composition rules, theories, architecture, spelling | fixed |
| DOC-2 | Doc | `docs/Standards_and_Tracker.md`, `docs/Continuation.md` | The 2026-10-22 docs called the `"ROTATING"` value a code bug (old F-4). The enum is correct; the README is what's wrong. | Corrected the same day | fixed |
| KN-2 | Bug / Dead | `logging_kernel/normalizers.py` | `normalize_level_name`: unknown strings quietly become `INFO`, integers are unchecked (`999` passes), and `try: return level / except InvalidLevelError` can never trigger. `InvalidLevelError` is never raised. (Project A `KN-7` is parked on this.) | Pass 1 | open |
| KN-3 | Consistency | `logging_kernel/normalizers.py` | Imports `ExperimentType`/`ProfileType` from `core.registry` at module top, which breaks the layering and creates a cycle that only works because of import order. It also re-imports them lazily inside the functions. | Pass 1 | open |
| KN-4 | Doc | `logging_kernel/errors.py` | Examples show lowercase valid names, but messages list the uppercase values. It says `normalize_exp_name` lives in `handlers`, and refers to `ExperimentFactory`/`ProfileFactory` (the real names are `LabExperiment`/`LabProfile`). | Pass 1 | open |
| KN-5 | Doc | `logging_kernel/handlers.py` | The `configure_handler` example uses the old `_configure_handler` name. | Pass 1 | open |
| KN-6 | Dead | `logging_kernel/formatters.py` | `build_console_formatter()` is never used. | Pass 1: remove it or document why it stays | open |
| KN-7 | Consistency | `constants.py`, `formatters.py`, `handlers.py`, `normalizers.py` | No module docstring. | Pass 1 | open |
| KN-8 | Dead | `logging_kernel/normalizers.py` | A `__main__` demo block with `_test_case`. | Pass 1: move it into tests | open |
| KN-9 | Consistency | `errors.py` (`_VALID`), `formatters.py` (`_STANDARD_ATTRS`) | `_` prefix with no stated reason. | Pass 1 | open |
| CR-3 | Doc | `core/registry.py` | Docstrings name `ExperimentFactory`/`ProfileFactory`. The `_validate_*` "positional parameter" wording also counts keyword-only parameters. | Pass 2 | open |
| CR-4 | Simplify | `core/registry.py` | The `VAR_POSITIONAL`/`VAR_KEYWORD` exclusion is written twice in the same comprehension, in both validators. | Pass 2 | open |
| CR-5 | Consistency | `core/registry.py` | The theory import sits halfway down the module, between the dicts and the helpers. Registration imports are at the bottom without a note on why (the cycle). | Pass 2 (after Step 5) **Done:** the theory import is gone; the theory registration note is at the bottom with the others | fixed |
| CR-6 | Consistency | `core/enums.py` | No module docstring. 5-space indentation. No note that member names may differ from values. | Pass 2 | open |
| CR-7 | Consistency | `__init__.py`, `core/builder.py`, profiles | Three different default levels: `get_logger` uses `DEBUG`, `LabBuilder` uses `INFO`, and `observer`/`minimalist` use `WARNING` (only when called directly). | Pass 2: owner to choose one rule | open |
| CR-8 | Consistency | `core/builder.py` | Every profile build leaves an empty `"<name>.__profile__"` logger in `logging`'s manager. | Pass 2 **Done:** `build()` no longer calls the profile function | fixed |
| EX-1 | Doc | `experiments/rotating_file.py` | Says backups are "compressed copies". Stdlib rotation doesn't compress. | Fixed with CR-9 (docstring rewritten anyway): "keeping *backup_count* older copies". | fixed |
| EX-2 | Doc | `experiments/standard.py` | Mentions `_configure_handler`. | Pass 3 | open |
| EX-3 | Consistency | `experiments/verbose.py` | `_VERBOSE_FMT`/`_DATE_FMT` have a `_` prefix with no reason. | Pass 3 | open |
| EX-4 | Consistency | `experiments/__init__.py` | No module docstring and no trailing newline. | Pass 3 | open |
| EX-5 | Doc | `experiments/file.py` | The module docstring says it's used by `conspiracy_theorist`, which becomes false after Step 1. | Fix in Step 1 | fixed |
| PF-2 | Consistency | `profiles/_base.py`, `profiles/__init__.py` | `_build_profile` has a private prefix but is exported in `__all__`. | Pass 4: pick one | open |
| PF-3 | Consistency | `profiles/__init__.py` | No module docstring. | Pass 4 | open |
| TH-3 | Consistency | `theories/*_exp.py` (6) | Design notes are `#` comments, not module docstrings. Four have no trailing newline. | Pass 5: Idea-stage format (§3.4) | open |
| PK-1 | Consistency | `src/__init__.py` | `src/` should not be a package, and its name ("Project D-bug") is out of date. (Its version was brought in line with `pyproject.toml` at 0.2.0, 2026-10-22.) | Pass 6: owner's call | open |
| PK-2 | Doc / Consistency | `logger_lab/__init__.py` | `get_experiment`, `get_profile` and `TheoryType` are imported but not in `__all__`. The `get_logger` docstring says "exactly one of profile or experiment", but `theory` counts too and both can be combined. | Pass 6 **Done:** `__all__` now lists `get_experiment`/`get_profile`/`get_theory`/`TheoryType`/`Channel` and the new errors; `get_logger` docstring corrected | fixed |
| PK-3 | Bug | `pyproject.toml` | No `[build-system]`, so uv never installs `logger_lab` into `.venv` (`import logger_lab` fails there). No dev dependencies (pytest, pyrefly). No `py.typed`. | Build system: `uv_build>=0.11.16,<0.12` added 2026-10-22. Verified: `uv sync` installs it as editable, it imports from outside the repo without `PYTHONPATH`, and `uv build` produces an sdist and wheel. `dev` group (pytest 9.1, pyrefly 1.4), `[tool.pytest.ini_options]`, `[tool.pyrefly]` and `py.typed` added 2026-10-22. | fixed |
| PK-5 | Consistency | `src/logger_lab/docs/` | The tracker docs live inside the package, so `uv build` ships them in the wheel to every user (seen in the 2026-10-22 build). | Owner's call: move them to a repo-root `docs/`, or exclude them from the wheel | open |
| PK-6 | Consistency | repository root | There is no `.gitignore`. `.venv` is ignored only because of uv's own inner ignore file. `logs/`, `dist/` and `__pycache__/` at the root are not ignored. | Add a root `.gitignore` **Done:** root `.gitignore` (venv, dist, caches, `logs/`, `.idea/workspace.xml`) | fixed |
| PK-4 | Consistency | `main.py` | Builds four loggers and creates log files when imported. | Pass 6: move under `__main__` | open |
| KN-10 | Bug | `logging_kernel/formatters.py` | `log_event()` calls `logger.log()` without `stacklevel=2`, so every structured record's `source` is `formatters.log_event:36`, not the caller (seen in `main.py`'s JSON output, 2026-10-22). This breaks the `source` field of the JSON standard. | Fix now (owner, 2026-10-22). **Done:** `stacklevel=2`; `test_log_event_source_is_the_caller`; `main.py`'s JSON now shows `main:32` | fixed |
| TS-3 | Test | `tests/conftest.py` | Tests must never log to a file inside the repository (owner, 2026-10-22). Until now this held only because of the `chdir` fixture; nothing enforced it. | **Done:** two guards. A test fails if any `FileHandler` it left points inside the repo, and the session fails if any `*.log*` file appeared in the repo (`.venv`/`.git` excluded). A deliberate probe test tripped both; the probe was then removed. | fixed |
| CR-9 | Design | `core/builder.py` | One-per-channel is enforced per logger. Two *loggers* can still share a file: the common `get_logger(__name__, profile="investigator")` in every module opens one `FileHandler` per module on `logs/app.log`. Appending works, but a shared `rotating_file` across loggers hits the same Windows rename lock as `PF-1`. Raising here would break that pattern (Project A's `logging_config.get_logger` alone has 34 callers). | Option A (owner, 2026-10-22) with D-11's rules. **Done:** `share_file_handler()`/`SHARED_FILES` in `handlers.py`; file experiments share by path; `tests/test_sharing.py` (11 tests). Project A's ~34 rotating module loggers will share one handler when they upgrade. | fixed |
| KN-11 | Design | `logging_kernel/formatters.py` | `JSONFormatter` doesn't output the logger's name. Text formats show `%(name)s`, but JSON only has `source.module`. Once several modules share one stream (CR-9 option A), JSON records can't be traced back to the logger that made them. | Owner's call: add a `"logger"` field (a v1 schema change) | open |
| CR-10 | Bug | `core/builder.py` | Rebuilding a logger that other threads are logging to isn't atomic. `build()` clears the old handlers and then adds the new ones one at a time, so a concurrent record can see no handlers or only some of them. | **Done:** `install_handlers()` builds every handler, swaps `logger.handlers` in one assignment under the table lock, then releases the old ones; a failing factory leaves the logger untouched. `StayClosedMixin` stops a released file handler from reopening for a thread still finishing a record (stdlib `FileHandler` reopens in append mode). `test_rebuilding_while_other_threads_log`. | fixed |
| TS-4 | Test | `tests/` | No thread-safety tests (D-9): concurrent logging from many threads, rotation under load, rebuilding while others log. | **Done:** `tests/test_threads.py`: concurrent builds open the file once; 8 threads × 400 records across rotations, every line whole and present exactly once; rebuilding mid-traffic 50×. Checked it can fail: with sharing patched out, the rotation test loses records and hits `WinError 32`. Passed 5 runs in a row. | fixed |
| KN-12 | Bug | `logging_kernel/handlers.py` | Rebuilding a logger closed **every** handler on it, including ones logger-lab never created. Found while building CR-9: pytest 9 attaches its capture handler to every non-propagating logger, and the rebuild closed it. A user's own handler shared by several loggers would have been closed for all of them. | **Done:** `configure_handler()` records logger-lab's handlers in `LAB_HANDLERS` (a weak set). `release_handler()` closes only those; foreign handlers are detached, never closed. `test_handlers_logger_lab_did_not_create_are_detached_not_closed`. | fixed |
| PK-7 | Consistency | `main.py`, `README.md` | The usage example built `conspiracy_theorist` (`ROTATING` on `logs/app.log`) and a `STANDARD` + `FILE` logger on the same file, which now raises `LogFileClashError` (D-11). | **Done:** the builder example uses `with_file_args(filename="builder.log")`; `main.py` runs clean. | fixed |
| TS-2 | Test | `tests/` | Coverage today: names, composition, file args, closing, rotation, registry, JSON schema. Not yet covered: `get_log_dir()` failure (`LogDirectoryError`), level normalization, `main.py`. | Grow with each pass | open |
| TS-1 | Test | `tests/` | No tests exist. | Set up the baseline (Standards §4) **Done:** 5 test files, 97 tests (98 after KN-10) | fixed |

Types: Bug · Doc · Dead · Consistency · Simplify · Efficiency · Test · Design.

### Old IDs from the first Standards doc (2026-10-22)

| Old | New | | Old | New |
|---|---|---|---|---|
| F-0 (`with_log_dir` + profile `TypeError`) | fixed before this ledger | | F-6 | KN-2 |
| F-1 | PF-1 | | F-7 | CR-7 |
| F-2 (`get_logger` has no file args) | Continuation D-4 | | F-8 | KN-3 |
| F-3 | KN-1 | | F-9 | KN-9, EX-3, PF-2 |
| F-4 | DOC-1 / DOC-2 (not a code bug) | | F-10 | CR-4 |
| F-5 | CR-2, TH-1 | | F-11 | CR-8 |

---

## Intentional (do not "fix")

- **Member names that differ from values** (`ROTATING_FILE`/`"ROTATING"`,
  `AGENT`/`"AI_AGENT"`, `CONSPIRATOR`/`"CONSPIRACY_THEORIST"`). Selection is
  by member or by value string; the member *name* as a string is not accepted.
- **`with_file_args()` replaces every arg on each call**, so omitted args go
  back to their defaults (Continuation D-6).
- **One set of file args is forwarded to every factory**, and factories ignore
  what they don't use (D-1).
- **Registration imports at the bottom of `registry.py`** exist to break the
  registry ↔ factories cycle. Document this (`CR-5`); don't move them up.
- **`LabFrame` relies on `ExperimentType.ROTATING_FILE`** for its
  feedback log. Keep that member working.

---

## Updating this doc

1. After each file: fill in its row (scores, tests, notes) and add its
   findings to the ledger with their decision.
2. After each pass: close the pass row, refresh its LOC, and note the commit.
3. After each Step from `Continuation.md`: mark its findings `fixed`, with how
   they were verified.
4. Carry anything left open into the ledger with an ID. Nothing open lives
   only in chat.
