# Cleanliness & Efficiency Tracker

This is the file-level review ledger for `logger_lab`. **Round 1 opened on
2026-10-22** at version **0.2.0** (commit `3adfa9c`). The ledger starts from
the project-wide review that day, and Phase 1 (Steps 0–5 in
`Continuation.md`) closed its findings the same day, and **every finding flagged
since was fixed on 2026-10-22** (owner-approved batch). The passes still run
file by file to score each file and look for anything new; 1.1 is closed.

**Purpose:** one place to see four things:

- how clean, efficient and tested every package and file is
- which passes are done
- what was found and fixed
- what is still open

The rules being checked against are in `Standards_and_Tracker.md`.

---

## How a pass works

A **pass** reviews one package, one file at a time, in the order its section
lists:

1. **Read and list.** I read the file in full, against the checklist below,
   score it, and list its findings by type, each with an ID. Non-trivial fixes
   come with a before/after. The file's row becomes `in review`.
2. **Decide.** The owner approves which findings get fixed. Nothing is written
   before that.
3. **Fix and verify.** I apply the approved fixes, then run `uv run pytest -q`
   and `uv run pyrefly check` from the repository root. Both must stay green
   (baseline: **112 passed**, **0 errors**). A behaviour fix lands with a test
   that fails without it.
4. **Re-score.** I re-rate the file and mark it `closed`, then move to the next
   file.
5. **Close.** After the last file, I review the package as a whole (structure,
   exports, duplication, layering, ownership), close the pass row, refresh its
   LOC, and the owner commits.

A finding that belongs to another file goes into the ledger with that file's
ID and waits for that file's pass. It isn't fixed early.

### The file checklist

| Check | Looks for |
|---|---|
| **Correctness** | Bugs and unhandled edge cases. Typed errors instead of bare `KeyError`/`TypeError`. Behaviour on Windows (file locks). |
| **Thread safety** | Standards §2.4: no shared mutable state without a lock, atomic handler swaps, nothing that opens a file except `share_file_handler()`. |
| **Contracts** | Extension points follow Standards §3.1 (`**kwargs`, `logger_name`, `configure_handler`, `get_log_dir`, the channel). Names resolve by member and by value. |
| **Truthful docs** | Docstrings, Args, Returns and Raises that match the code, with no stale names (`_configure_handler`, `*Factory`, `normalisers`). Docstrings follow Standards §1.3. |
| **Dead code** | Unused imports, parameters, functions or constants; branches that can never run. |
| **Consistency** | Standards §1.4: module docstring, trailing newline, `X \| None` typing, keyword arguments at call sites, American spelling, `_` prefixes only with a stated reason, `__all__` matching imports, banners. |
| **Layering and ownership** | Imports point down only (below); every concern stays with its one owner (Standards §2.6). |
| **Simplicity** | Duplication, overlong functions, deep nesting, magic numbers that belong in `constants`. |
| **Efficiency** | Repeated work on the emit path. Setup work repeated per record. |
| **Tests** | The file's behaviour is pinned by an offline test. |

**Layering rule:** imports point down only:
constants ← errors ← formatters/handlers ← enums ← normalizers ←
experiments/theories ← profiles ← registry ← builder ← `__init__`.

**Pass 7 (tests) checks instead:**
- each test pins behaviour a consumer depends on; tests that only restate
  the obvious are removed and listed;
- tests are offline and deterministic, write only inside `tmp_path`, and
  release what they open;
- concurrency tests are shown to fail without their fix;
- names and docstrings say what is being pinned.

**Pass 8 (docs) checks instead:** every claim matches the code at the
current commit; examples run; IDs, versions and counts are current; each doc
sticks to what it owns (Standards header table).

### Scores

| Score | Clean | Eff |
|---|---|---|
| 9–10 | Truthful docs, consistent style and typing, no dead code, clear names | No redundant work on the emit path; setup work done once |
| 7–8 | Minor nits: spacing, comment fluff, stale wording | Small redundant work, tolerable |
| ≤6 | Docs that are wrong, dead checks, bad names, structural duplication | Real waste (per-record work that could be done once) |

**Tests:** ✓ behaviour covered · partial · none · n/a (nothing to test). Marked
from the 0.2.0 suite; each pass re-checks its own files.
**Status:** `closed` = reviewed, fixed, re-rated · `in review` · `pending`.

**Finding IDs:** `KN-` logging_kernel · `CR-` core · `EX-` experiments ·
`PF-` profiles · `TH-` theories · `PK-` package root and packaging · `TS-`
tests · `DOC-` README and docs. New IDs continue each prefix's numbering.

---

## Round 1 passes

Passes run bottom-up through the layering, so each file is reviewed after
everything it imports.

| # | Pass | Files | LOC | Clean | Eff | Open findings | Status |
|---|---|---:|---:|---:|---:|---:|---|
| 1 | `logging_kernel` | 7 | 1,276 + new | — | — | 1 | **in review** (1 of 7 closed) |
| 2 | `core` | 4 | 855 | — | — | 0 | pending |
| 3 | `experiments` | 9 | 385 + new | — | — | 1 | pending |
| 4 | `profiles` | 7 | 231 + new | — | — | 0 | pending |
| 5 | `theories` | 11 | 74 ± | — | — | 0 | pending |
| 6 | Package root | 3 | 222 | — | — | 0 | pending |
| 7 | `tests/` | 13 | 813 + new | — | — | 0 | pending |
| 8 | README + `docs/` | 7 | 1,630 | — | — | 0 | pending |
| — | **Total** | **60** | **5,486 at `3adfa9c`, + new files** | | | **2** | 0 of 8 closed |

LOC counted 2026-10-22 at `3adfa9c` (0.2.0), before any pass. Files added
after that commit (async, relay, `gui`, `TIMED_FILE`; still 0.2.0) are marked
*(new after `3adfa9c`)* with their own LOC; pass LOC is refreshed when each
pass closes. (The very first
count, before Phase 1, was 2,123 lines of Python in `src/`.) `py.typed` and
`.python-version` are listed under the package root but have no content to
review.

---

## File-level detail

### 1. logging_kernel: in review

Order: `constants` → `errors` → `formatters` → `handlers` → `dispatch` →
`normalizers` → `__init__`.

| # | File | LOC | Clean | Eff | Tests | Open findings | Status |
|---|---|---:|---:|---:|---|---|---|
| 1.1 | `constants.py` | 15 | 10 | 10 | n/a | — (fixed: `KN-7` part, `KN-13`, `KN-14`, `KN-15`) | **closed** |
| 1.2 | `errors.py` | 499 | — | — | partial | — (fixed: `KN-4`, `KN-9`) | pending |
| 1.3 | `formatters.py` | 152 | — | — | partial | — (fixed: `KN-6`, `KN-7`, `KN-9`, `KN-11`, `KN-17`) | pending |
| 1.4 | `handlers.py` | 354 | — | — | ✓ | — (fixed: `KN-5`, `KN-7`, `KN-16`) | pending |
| 1.4b | `dispatch.py` *(new after `3adfa9c`)* | 239 | — | — | ✓ | `KN-19` (fixed: `KN-18`) | pending |
| 1.5 | `normalizers.py` | 166 | — | — | partial | — (fixed: `KN-2`, `KN-3`, `KN-7`, `KN-8`) | pending |
| 1.6 | `__init__.py` | 104 | — | — | n/a | — | pending |

Fixed before the pass: `KN-1`, `KN-10`, `KN-12` (and `CR-9`/`CR-10` landed in `handlers.py`).

### 2. core: pending

Order: `enums` → `registry` → `builder` → `__init__`.

| # | File | LOC | Clean | Eff | Tests | Open findings | Status |
|---|---|---:|---:|---:|---|---|---|
| 2.1 | `enums.py` | 41 | — | — | ✓ | — (fixed: `CR-6`) | pending |
| 2.2 | `registry.py` | 436 | — | — | ✓ | — (fixed: `CR-3`, `CR-4`) | pending |
| 2.3 | `builder.py` | 349 | — | — | ✓ | — (fixed: `CR-7`) | pending |
| 2.4 | `__init__.py` | 29 | — | — | n/a | — | pending |

Fixed before the pass: `CR-1`, `CR-2`, `CR-5`, `CR-8`, `CR-9`, `CR-10`.

### 3. experiments: pending

Order: `standard` → `verbose` → `minimalist` → `ai` → `file` →
`rotating_file` → `relay` → `asynchronous` → `__init__` (console, JSON, file,
live, then the dispatcher).

| # | File | LOC | Clean | Eff | Tests | Open findings | Status |
|---|---|---:|---:|---:|---|---|---|
| 3.1 | `standard.py` | 48 | — | — | ✓ | — (fixed: `EX-2`) | pending |
| 3.2 | `verbose.py` | 49 | — | — | ✓ | — (fixed: `EX-3`, `EX-6`) | pending |
| 3.3 | `minimalist.py` | 43 | — | — | ✓ | — | pending |
| 3.4 | `ai.py` | 53 | — | — | ✓ | — | pending |
| 3.5 | `file.py` | 76 | — | — | ✓ | — | pending |
| 3.6 | `rotating_file.py` | 101 | — | — | ✓ | — | pending |
| 3.6b | `relay.py` *(new after `3adfa9c`)* | 69 | — | — | ✓ | `EX-7` | pending |
| 3.6c | `asynchronous.py` *(new after `3adfa9c`)* | 60 | — | — | ✓ | — | pending |
| 3.7 | `__init__.py` | 15 | — | — | n/a | — (fixed: `EX-4`) | pending |

Fixed before the pass: `EX-1`, `EX-5`.

### 4. profiles: pending

Order: `base` → `observer` → `investigator` → `conspiracy_theorist` →
`ai_agent` → `gui` → `__init__`.

| # | File | LOC | Clean | Eff | Tests | Open findings | Status |
|---|---|---:|---:|---:|---|---|---|
| 4.1 | `base.py` (was `_base.py`) | 58 | — | — | ✓ | — (fixed: `PF-2`) | pending |
| 4.2 | `observer.py` | 36 | — | — | ✓ | — (fixed: `PF-4`) | pending |
| 4.3 | `investigator.py` | 39 | — | — | ✓ | — (fixed: `PF-4`) | pending |
| 4.4 | `conspiracy_theorist.py` | 39 | — | — | ✓ | — (fixed: `PF-4`) | pending |
| 4.5 | `ai_agent.py` | 46 | — | — | ✓ | — (fixed: `PF-4`) | pending |
| 4.5b | `gui.py` *(new after `3adfa9c`)* | 48 | — | — | ✓ | — | pending |
| 4.6 | `__init__.py` | 13 | — | — | n/a | — (fixed: `PF-2`, `PF-3`) | pending |

Fixed before the pass: `PF-1`.

### 5. theories: pending

Order: `timed_file_exp` → `trace_exp` → `lifecycle_exp` → `throttle_exp` →
`performance_exp` → `process_exp` → `http_exp` → `sec_exp` → `db_exp` (the
roadmap's rank order, D-20) → `_test_theory` → `__init__`. The eight idea files
are reviewed against the Idea stage format (Standards §3.4), not as working code. (`async_exp.py` was removed when ASYNC
was promoted.)

| # | File | LOC | Clean | Eff | Tests | Open findings | Status |
|---|---|---:|---:|---:|---|---|---|
| 5.1 | `timed_file_exp.py` *(trial, after `3adfa9c`)* | 84 | — | — | ✓ | — | pending |
| 5.2 | `trace_exp.py` | 9 | — | — | n/a | — (fixed: `TH-3`) | pending |
| 5.3 | `lifecycle_exp.py` *(new after `00d28fd`)* | 13 | — | — | n/a | — (Idea stage) | pending |
| 5.4 | `throttle_exp.py` *(new after `00d28fd`)* | 12 | — | — | n/a | — (Idea stage) | pending |
| 5.5 | `performance_exp.py` | 8 | — | — | n/a | — (fixed: `TH-3`) | pending |
| 5.6 | `process_exp.py` *(new after `00d28fd`)* | 11 | — | — | n/a | — (Idea stage) | pending |
| 5.7 | `http_exp.py` | 8 | — | — | n/a | — (fixed: `TH-3`) | pending |
| 5.8 | `sec_exp.py` | 8 | — | — | n/a | — (fixed: `TH-3`) | pending |
| 5.9 | `db_exp.py` | 8 | — | — | n/a | — (fixed: `TH-3`) | pending |
| 5.10 | `_test_theory.py` | 33 | — | — | n/a | — | pending |
| 5.11 | `__init__.py` | 4 | — | — | n/a | — | pending |

Fixed before the pass: `TH-1`, `TH-2`.

### 6. Package root: pending

Order: `logger_lab/__init__.py` → `pyproject.toml` → `.gitignore`.

| # | File | LOC | Clean | Eff | Tests | Open findings | Status |
|---|---|---:|---:|---:|---|---|---|
| 6.1 | `logger_lab/__init__.py` | 135 | — | — | ✓ | — | pending |
| 6.2 | ~~`main.py`~~ | — | — | — | — | deleted (`PK-4`) | **removed** |
| 6.3 | ~~`src/__init__.py`~~ | — | — | — | — | deleted (`PK-1`) | **removed** |
| 6.4 | `pyproject.toml` | 25 | — | — | n/a | — (fixed: `PK-5`) | pending |
| 6.5 | `.gitignore` | 16 | — | — | n/a | — | pending |

Fixed before the pass: `PK-2`, `PK-3`, `PK-6`, `PK-7`. (`PK-5`, the docs
shipping in the wheel, is listed on `pyproject.toml` because that's where an
exclusion would go, if the owner keeps the docs where they are.)

### 7. tests: pending

Order: `conftest` → `test_names` → `test_composition` → `test_files` →
`test_sharing` → `test_threads` → `test_registry` → `test_formatters` →
`test_async` → `test_relay` → `test_gui` → `test_timed_file` → `test_levels`.

| # | File | LOC | Tests | Clean | Covers | Open findings | Status |
|---|---|---:|---:|---:|---|---|---|
| 7.1 | `conftest.py` | 73 | — | — | Each test runs in `tmp_path`; handlers released afterwards; guards fail any test or run that logs inside the repo (`TS-3`) or leaks a shared file | — | pending |
| 7.2 | `test_names.py` | 82 | 56 | — | Member, value and lowercase for every experiment, profile and theory; renamed members rejected | — | pending |
| 7.3 | `test_composition.py` | 115 | 14 | — | Channels, clashes, duplicates, untouched-on-error, conspiracy_theorist | — | pending |
| 7.4 | `test_files.py` | 97 | 15 | — | Defaults, file args everywhere, rotating args, closing, Windows rotation | — | pending |
| 7.5 | `test_sharing.py` | 146 | 11 | — | One handler per file across loggers, per-module levels and experiments, clash, first-wins warning, sole-owner rebuild, last-release close, foreign handlers untouched, no reopen after close | — | pending |
| 7.6 | `test_threads.py` | 116 | 3 | — | Concurrent builds, 8-thread rotation without losing a line, rebuilding mid-traffic | — | pending |
| 7.7 | `test_registry.py` | 102 | 9 | — | Clashing or unregistered profile compositions, profile function = declaration, theory registration and options | — | pending |
| 7.8 | `test_formatters.py` | 126 | 7 | — | JSON v1.1 fields, exceptions and stack (also through async), `log_event` extra and caller source, non-serializable fallback | — | pending |
| 7.9 | `test_async.py` *(new after `3adfa9c`)* | 219 | 12 | — | One handler, worker thread, tracebacks kept, message frozen, order, one worker per process, needs an output, release drains, drain from worker, restart, 8-thread rotation | — | pending |
| 7.10 | `test_relay.py` *(new after `3adfa9c`)* | 72 | 5 | — | Subscriber gets records, brings relay, per-subscriber level, none = no handler, failing callback reported | — | pending |
| 7.11 | `test_gui.py` *(new after `3adfa9c`)* | 80 | 4 | — | Shape, LabFrame-style child propagation off-thread with no stdout, many job threads, direct call | — | pending |
| 7.12 | `test_timed_file.py` *(new after `3adfa9c`)* | 91 | 6 | — | Defaults, options, forced rollover on Windows, sharing, clashes, behind async | — | pending |
| 7.13 | `test_levels.py` *(new after `3adfa9c`)* | 98 | 27 | — | Accepted and rejected levels, custom names, every entry point validates, the INFO/WARNING default rule, `LogDirectoryError`, public `build_profile` | — | pending |

Suite-level: `TS-2` (coverage gaps: `LogDirectoryError`, level normalization,
`main.py`). Fixed before the pass: `TS-1`, `TS-3`, `TS-4`.

### 8. README + docs: pending

Order: `README.md` → `API_Reference.md` → `Standards_and_Tracker.md` →
`Continuation.md` → `Framework_Comparison.md` → `Cleanliness_Tracker.md`
(last, so it records the pass itself).

| # | File | LOC | Clean | Open findings | Status |
|---|---|---:|---:|---|---|
| 8.1 | `README.md` | 449 | — | — | pending |
| 8.2 | `docs/API_Reference.md` (repo root) | 305 | — | — | pending |
| 8.3 | `docs/Standards_and_Tracker.md` | 350 | — | — | pending |
| 8.4 | `docs/Continuation.md` | 164 | — | — | pending |
| 8.5 | `docs/Framework_Comparison.md` | 90 | — | — | pending |
| 8.5b | `docs/Feedback_Guide.md` *(new after `3adfa9c`)* | 281 | — | — | pending |
| 8.6 | `docs/Cleanliness_Tracker.md` | 272 | — | — | pending |

Fixed before the pass: `DOC-1`, `DOC-2`. (`PK-5`, whether these docs ship in
the wheel, is decided in pass 6.)

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
| KN-2 | Bug / Dead | `logging_kernel/normalizers.py` | `normalize_level_name`: unknown strings quietly become `INFO`, integers are unchecked (`999` passes), and `try: return level / except InvalidLevelError` can never trigger. `InvalidLevelError` is never raised. (Project A `KN-7` is parked on this.) | Owner, 2026-10-22: invalid levels raise. **Done:** unknown names, negatives and non-integers raise `InvalidLevelError`; names via the stdlib's level table (custom names too); `tests/test_levels.py`. | fixed |
| KN-3 | Consistency | `logging_kernel/normalizers.py` | Imports `ExperimentType`/`ProfileType` from `core.registry` at module top, which breaks the layering and creates a cycle that only works because of import order. It also re-imports them lazily inside the functions. | **Done:** the enums are a `TYPE_CHECKING`-only import; each function imports them lazily, so `normalizers` no longer loads the registry. | fixed |
| KN-4 | Doc | `logging_kernel/errors.py` | Examples show lowercase valid names, but messages list the uppercase values. It says `normalize_exp_name` lives in `handlers`, and refers to `ExperimentFactory`/`ProfileFactory` (the real names are `LabExperiment`/`LabProfile`). | **Done:** examples match the real messages (uppercase values, enum order), `normalizers` module named, `LabExperiment`/`LabProfile`; messages now say "recognized". | fixed |
| KN-5 | Doc | `logging_kernel/handlers.py` | The `configure_handler` example uses the old `_configure_handler` name. | **Done:** example uses `configure_handler`. | fixed |
| KN-6 | Dead | `logging_kernel/formatters.py` | `build_console_formatter()` is never used. | Owner, 2026-10-22. **Done:** removed with its export. | fixed |
| KN-7 | Consistency | `constants.py`, `formatters.py`, `handlers.py`, `normalizers.py` | No module docstring. | **Done:** `formatters.py`, `normalizers.py` (and `constants.py` in 1.1); `handlers.py` already had one. | fixed |
| KN-8 | Dead | `logging_kernel/normalizers.py` | A `__main__` demo block with `_test_case`. | **Done:** demo block and `_test_case` deleted; tests cover it. | fixed |
| KN-9 | Consistency | `errors.py` (`_VALID`), `formatters.py` (`_STANDARD_ATTRS`) | `_` prefix with no stated reason. | **Done:** `InvalidLevelError.VALID`, `JSONFormatter.STANDARD_ATTRS`. | fixed |
| CR-3 | Doc | `core/registry.py` | Docstrings name `ExperimentFactory`/`ProfileFactory`. The `_validate_*` "positional parameter" wording also counts keyword-only parameters. | **Done:** `LabProfile` named; "named parameter" wording (``*args``/``**kwargs`` don't count). | fixed |
| CR-4 | Simplify | `core/registry.py` | The `VAR_POSITIONAL`/`VAR_KEYWORD` exclusion is written twice in the same comprehension, in both validators. | **Done:** one condition in each validator. | fixed |
| CR-5 | Consistency | `core/registry.py` | The theory import sits halfway down the module, between the dicts and the helpers. Registration imports are at the bottom without a note on why (the cycle). | Pass 2 (after Step 5) **Done:** the theory import is gone; the theory registration note is at the bottom with the others | fixed |
| CR-6 | Consistency | `core/enums.py` | No module docstring. 5-space indentation. No note that member names may differ from values. | **Done:** module docstring (incl. names vs values), 4-space indentation, class docstrings. | fixed |
| CR-7 | Consistency | `__init__.py`, `core/builder.py`, profiles | Three different default levels: `get_logger` uses `DEBUG`, `LabBuilder` uses `INFO`, and `observer`/`minimalist` use `WARNING` (only when called directly). | Owner, 2026-10-22: INFO, WARNING for observer/minimalist. **Done:** `default_level(plan)` in the builder; `get_logger(level=None)`; factories and profiles default to INFO (minimalist/observer WARNING); `tests/test_levels.py`. | fixed |
| CR-8 | Consistency | `core/builder.py` | Every profile build leaves an empty `"<name>.__profile__"` logger in `logging`'s manager. | Pass 2 **Done:** `build()` no longer calls the profile function | fixed |
| EX-1 | Doc | `experiments/rotating_file.py` | Says backups are "compressed copies". Stdlib rotation doesn't compress. | Fixed with CR-9 (docstring rewritten anyway): "keeping *backup_count* older copies". | fixed |
| EX-2 | Doc | `experiments/standard.py` | Mentions `_configure_handler`. | **Done:** names `configure_handler`. | fixed |
| EX-3 | Consistency | `experiments/verbose.py` | `_VERBOSE_FMT`/`_DATE_FMT` have a `_` prefix with no reason. | **Done:** `VERBOSE_FMT`, `DATE_FMT`. | fixed |
| EX-4 | Consistency | `experiments/__init__.py` | No module docstring and no trailing newline. | **Done:** docstring and trailing newline. | fixed |
| EX-5 | Doc | `experiments/file.py` | The module docstring says it's used by `conspiracy_theorist`, which becomes false after Step 1. | Fix in Step 1 | fixed |
| PF-2 | Consistency | `profiles/_base.py`, `profiles/__init__.py` | `_build_profile` has a private prefix but is exported in `__all__`. | Owner, 2026-10-22. **Done:** `profiles/base.py` with a public, documented `build_profile`; `test_build_profile_is_public`. | fixed |
| PF-3 | Consistency | `profiles/__init__.py` | No module docstring. | **Done:** module docstring. | fixed |
| TH-3 | Consistency | `theories/*_exp.py` (5; `async_exp.py` removed when ASYNC was promoted) | Design notes are `#` comments, not module docstrings. Four have no trailing newline. | **Done:** Idea-stage module docstrings (mechanism, purpose, not registered); trailing newlines; `theories/__init__.py` docstring too. | fixed |
| PK-1 | Consistency | `src/__init__.py` | `src/` should not be a package, and its name ("Project D-bug") is out of date. (Its version was brought in line with `pyproject.toml` at 0.2.0, 2026-10-22.) | Owner, 2026-10-22. **Done:** `src/__init__.py` deleted. | fixed |
| PK-2 | Doc / Consistency | `logger_lab/__init__.py` | `get_experiment`, `get_profile` and `TheoryType` are imported but not in `__all__`. The `get_logger` docstring says "exactly one of profile or experiment", but `theory` counts too and both can be combined. | Pass 6 **Done:** `__all__` now lists `get_experiment`/`get_profile`/`get_theory`/`TheoryType`/`Channel` and the new errors; `get_logger` docstring corrected | fixed |
| PK-3 | Bug | `pyproject.toml` | No `[build-system]`, so uv never installs `logger_lab` into `.venv` (`import logger_lab` fails there). No dev dependencies (pytest, pyrefly). No `py.typed`. | Build system: `uv_build>=0.11.16,<0.12` added 2026-10-22. Verified: `uv sync` installs it as editable, it imports from outside the repo without `PYTHONPATH`, and `uv build` produces an sdist and wheel. `dev` group (pytest 9.1, pyrefly 1.4), `[tool.pytest.ini_options]`, `[tool.pyrefly]` and `py.typed` added 2026-10-22. | fixed |
| PK-5 | Consistency | `src/logger_lab/docs/` | The tracker docs live inside the package, so `uv build` ships them in the wheel to every user (seen in the 2026-10-22 build). | Owner, 2026-10-22. **Done:** docs moved to a repo-root `docs/`; the wheel no longer contains them. | fixed |
| PK-6 | Consistency | repository root | There is no `.gitignore`. `.venv` is ignored only because of uv's own inner ignore file. `logs/`, `dist/` and `__pycache__/` at the root are not ignored. | Add a root `.gitignore` **Done:** root `.gitignore` (venv, dist, caches, `logs/`, `.idea/workspace.xml`) | fixed |
| PK-4 | Consistency | `main.py` | Builds four loggers and creates log files when imported. | Owner, 2026-10-22: no longer needed. **Done:** `main.py` deleted (the README and docs carry the examples). | fixed |
| KN-10 | Bug | `logging_kernel/formatters.py` | `log_event()` calls `logger.log()` without `stacklevel=2`, so every structured record's `source` is `formatters.log_event:36`, not the caller (seen in `main.py`'s JSON output, 2026-10-22). This breaks the `source` field of the JSON standard. | Fix now (owner, 2026-10-22). **Done:** `stacklevel=2`; `test_log_event_source_is_the_caller`; `main.py`'s JSON now shows `main:32` | fixed |
| TS-3 | Test | `tests/conftest.py` | Tests must never log to a file inside the repository (owner, 2026-10-22). Until now this held only because of the `chdir` fixture; nothing enforced it. | **Done:** two guards. A test fails if any `FileHandler` it left points inside the repo, and the session fails if any `*.log*` file appeared in the repo (`.venv`/`.git` excluded). A deliberate probe test tripped both; the probe was then removed. | fixed |
| CR-9 | Design | `core/builder.py` | One-per-channel is enforced per logger. Two *loggers* can still share a file: the common `get_logger(__name__, profile="investigator")` in every module opens one `FileHandler` per module on `logs/app.log`. Appending works, but a shared `rotating_file` across loggers hits the same Windows rename lock as `PF-1`. Raising here would break that pattern (Project A's `logging_config.get_logger` alone has 34 callers). | Option A (owner, 2026-10-22) with D-11's rules. **Done:** `share_file_handler()`/`SHARED_FILES` in `handlers.py`; file experiments share by path; `tests/test_sharing.py` (11 tests). Project A's ~34 rotating module loggers will share one handler when they upgrade. | fixed |
| KN-11 | Design | `logging_kernel/formatters.py` | `JSONFormatter` doesn't output the logger's name. Text formats show `%(name)s`, but JSON only has `source.module`. Once several modules share one stream (CR-9 option A), JSON records can't be traced back to the logger that made them. | Owner, 2026-10-22. **Done:** top-level `"logger"` (Standard v1.1); `test_plain_record_has_the_v1_1_fields`. | fixed |
| KN-13 | Doc | `logging_kernel/constants.py` | The encoding comment said it "shouldn't be changed anyhow", but encoding is a public file arg (`with_file_args(encoding=...)`, which a test covers). | **Done (1.1):** the comment now says how to override it. | fixed |
| KN-14 | Consistency | `logging_kernel/constants.py` | `'utf-8'` and `'app.log'` were the package's only single-quoted strings (31 others use double quotes). | **Done (1.1):** double quotes. Each comment is now on the same line as its constant, in plain `#` (owner's comment rule, 2026-10-22). | fixed |
| KN-15 | Correctness | `logging_kernel/constants.py` | Reassigning a constant at runtime does nothing, because the defaults are fixed in function signatures when they're defined (verified: `file_experiment` keeps `logs`). A consumer could try it and fail silently. | **Done (1.1):** the module docstring says so and points to `with_file_args()`. `Final` was declined by the owner as unnecessary. | fixed |
| KN-17 | Design | `logging_kernel/formatters.py` | `JSONFormatter` drops exceptions: `exc_info`, `exc_text` and `stack_info` are excluded as standard attributes and never serialized, so `logger.exception()` through `ai` gives JSON with no traceback (verified 2026-10-22). It predates the async work (async itself keeps `exc_info`; text outputs write the traceback). | Owner, 2026-10-22. **Done:** `"exception": {type, message, traceback}` and `"stack"` (Standard v1.1); tests for both, and end to end through `async`. | fixed |
| KN-18 | Consistency | `logging_kernel/dispatch.py` | Comments for `DISPATCHERS`, `pending`/`pending_changed` and `worker`/`worker_lock`/`exit_hook_registered` sit on the lines above them, against the owner's comment rule (a constant's comment goes on its own line). Written during the async work, after the rule was added. | **Done:** plain `#` on each constant's line. | fixed |
| EX-7 | Correctness | `experiments/relay.py` | A subscriber that logs to a logger which relays back to it re-enters itself without end: one `info()` produced 50 records before a probe's cap (2026-10-22). Documented in `Feedback_Guide.md` §3. | Owner's call: a re-entry guard in `RelayHandler` (skip records logged *from inside* a subscriber on the same thread), or keep it documented | open |
| KN-19 | Design | `logging_kernel/dispatch.py` | One worker thread means one slow output delays every async logger: a 200 ms subscriber held back a record on an unrelated logger by about 212 ms (2026-10-22). This is the trade-off for strict ordering and one thread. Documented in `Feedback_Guide.md` §3. | Owner's call: keep and document (done); or later, per-subscriber hand-off queues / a timeout warning | open |
| KN-16 | Consistency | `logging_kernel/handlers.py` | Six `#:` comments sit above their constants (`UNNAMED`, `HandlerT`, `SHARED_FILES`, `LAB_HANDLERS`, `SHARED_FILES_LOCK`), against the owner's comment rule: plain `#`, on the same line. | **Done:** plain `#` on each constant's line. | fixed |
| EX-6 | Consistency | `experiments/verbose.py` | Two `#:` comments sit above `_VERBOSE_FMT` and `_DATE_FMT`, against the owner's comment rule: plain `#`, on the same line. | **Done:** plain `#` on each constant's line. | fixed |
| PF-4 | Consistency | `profiles/observer.py`, `investigator.py`, `conspiracy_theorist.py`, `ai_agent.py` | Each `*_EXPERIMENTS` tuple has a `#:` comment above it, against the owner's comment rule: plain `#`, on the same line. | **Done:** plain `#` on each tuple's line. | fixed |
| CR-10 | Bug | `core/builder.py` | Rebuilding a logger that other threads are logging to isn't atomic. `build()` clears the old handlers and then adds the new ones one at a time, so a concurrent record can see no handlers or only some of them. | **Done:** `install_handlers()` builds every handler, swaps `logger.handlers` in one assignment under the table lock, then releases the old ones; a failing factory leaves the logger untouched. `StayClosedMixin` stops a released file handler from reopening for a thread still finishing a record (stdlib `FileHandler` reopens in append mode). `test_rebuilding_while_other_threads_log`. | fixed |
| TS-4 | Test | `tests/` | No thread-safety tests (D-9): concurrent logging from many threads, rotation under load, rebuilding while others log. | **Done:** `tests/test_threads.py`: concurrent builds open the file once; 8 threads × 400 records across rotations, every line whole and present exactly once; rebuilding mid-traffic 50×. Checked it can fail: with sharing patched out, the rotation test loses records and hits `WinError 32`. Passed 5 runs in a row. | fixed |
| KN-12 | Bug | `logging_kernel/handlers.py` | Rebuilding a logger closed **every** handler on it, including ones logger-lab never created. Found while building CR-9: pytest 9 attaches its capture handler to every non-propagating logger, and the rebuild closed it. A user's own handler shared by several loggers would have been closed for all of them. | **Done:** `configure_handler()` records logger-lab's handlers in `LAB_HANDLERS` (a weak set). `release_handler()` closes only those; foreign handlers are detached, never closed. `test_handlers_logger_lab_did_not_create_are_detached_not_closed`. | fixed |
| PK-7 | Consistency | `main.py`, `README.md` | The usage example built `conspiracy_theorist` (`ROTATING` on `logs/app.log`) and a `STANDARD` + `FILE` logger on the same file, which now raises `LogFileClashError` (D-11). | **Done:** the builder example uses `with_file_args(filename="builder.log")`; `main.py` runs clean. | fixed |
| TS-2 | Test | `tests/` | Coverage today: names, composition, file args, closing, rotation, registry, JSON schema. Not yet covered: `get_log_dir()` failure (`LogDirectoryError`), level normalization, `main.py`. | **Done:** `LogDirectoryError` and level handling now tested (`tests/test_levels.py`); `main.py` deleted. | fixed |
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
