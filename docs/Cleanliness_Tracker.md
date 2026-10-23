# Cleanliness & Efficiency Tracker

This is the file-level review ledger for `logger_lab`. **Round 1 opened on
2026-10-22** at version **0.2.0** (commit `3adfa9c`). The ledger starts from
the project-wide review that day. Phase 1 (Steps 0–5 in `Continuation.md`)
closed its findings the same day, and **every finding flagged since was fixed
on 2026-10-22** (owner-approved batch). The same day, the
**four-kinds redesign** (`CR-11`) replaced experiments, channels and profile
functions with outputs, features, formats, catalysts and profile recipes, so
the pass tables below list the new files. The passes still run file by file
to score each file and look for anything new; 1.1 is closed.

**Round 1 closed 2026-10-23:** all eight passes are closed and every finding
is fixed. **Resumed 2026-10-23:** the passes ran in the order below, with the
owner, file by file. Each file is also checked against the IDE's own
inspections (PyCharm warnings and grammar), which the owner shares as each
file comes up; `pytest`, `pyrefly` (0 diagnostics) and a warnings-as-errors
import were clean when the pass resumed.

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
   (baseline: **190 passed**, **0 errors**). A behavior fix lands with a test
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
| **Correctness** | Bugs and unhandled edge cases. Typed errors instead of bare `KeyError`/`TypeError`. Behavior on Windows (file locks). |
| **Thread safety** | Standards §2.4: no shared mutable state without a lock, atomic handler swaps, nothing that opens a file except `share_file_handler()`. |
| **Contracts** | Extension points follow Standards §3.1 (a spec of the right kind, declared options and defaults, `configure_handler`, `get_log_dir`, `share_file_handler`). Names resolve by member and by value. |
| **Truthful docs** | Docstrings, Args, Returns and Raises that match the code, with no stale names (`_configure_handler`, `*Factory`, `normalisers`). Docstrings follow Standards §1.3. |
| **Dead code** | Unused imports, parameters, functions or constants; branches that can never run. |
| **Consistency** | Standards §1.4: short sentences joined with periods (no em dashes), module docstring, trailing newline, `X \| None` typing, keyword arguments at call sites, American spelling, `_` prefixes only with a stated reason, `__all__` matching imports, banners. |
| **Layering and ownership** | Imports point down only (below); every concern stays with its one owner (Standards §2.6). |
| **Simplicity** | Duplication, overlong functions, deep nesting, magic numbers that belong in `constants`. |
| **Efficiency** | Repeated work on the emit path. Setup work repeated per record. |
| **Tests** | The file's behavior is pinned by an offline test. |

**Layering rule:** imports point down only:
constants ← errors ← rollover/formatters/handlers/dispatch ← enums ← specs ←
normalizers ← outputs/features/formats/catalysts/theories ← profiles ←
registry ← builder ← `__init__`.

**Pass 7 (tests) checks instead:**
- each test pins behavior a consumer depends on; tests that only restate
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

**Tests:** ✓ behavior covered · partial · none · n/a (nothing to test). A blank
score or test cell means the file isn't scored yet. Marked
from the 0.2.0 suite; each pass re-checks its own files.
**Status:** `closed` = reviewed, fixed, re-rated · `in review` · `pending`.

**Finding IDs:** `KN-` logging_kernel · `CR-` core · `EX-` building blocks
(outputs, features, formats, catalysts; it was experiments) · `PF-` profiles ·
`TH-` theories · `PK-` package root and packaging · `TS-` tests · `DOC-`
README and docs. New IDs continue each prefix's numbering.

---

## Round 1 passes

Passes run bottom-up through the layering, so each file is reviewed after
everything it imports.

| # | Pass | Files | LOC | Clean | Eff | Open findings | Status |
|---|---|---:|---:|---:|---:|---:|---|
| 1 | `logging_kernel` | 8 | 1,784 | 9 | 9 | 0 | **closed** 2026-10-23 |
| 2 | `core` | 5 | 1,131 | 10 | 10 | 0 | **closed** 2026-10-23 |
| 3 | Building blocks (`outputs`, `features`, `formats`, `catalysts`) | 10 | 591 | 10 | 10 | 0 | **closed** 2026-10-23 |
| 4 | `profiles` | 6 | 203 | 10 | 10 | 0 | **closed** 2026-10-23 |
| 5 | `theories` | 9 | 124 | 10 |  | 0 | **closed** 2026-10-23 |
| 6 | Package root | 3 | 141 | 10 | 10 | 0 | **closed** 2026-10-23 |
| 7 | `tests/` | 15 | 2,207 | 10 |  | 0 | **closed** 2026-10-23 |
| 8 | README + `docs/` | 7 | 2,649 | 10 |  | 0 | **closed** 2026-10-23 |
|  | **Total** | **63** | **8,830** | | | **0** | 8 of 8 closed |

LOC recounted 2026-10-23, after the four-kinds redesign (`CR-11`) and the
test redesign (`TS-5`), still 0.2.0; the first count at `3adfa9c` was 5,486, and before Phase 1 there
were 2,123 lines of Python in `src/`. Pass LOC is refreshed again when each
pass closes. `py.typed` and `.python-version` are listed under the package
root but have no content to review.

---

## File-level detail

### 1. logging_kernel: closed

Order: `constants` → `errors` → `rollover` → `formatters` → `handlers` →
`dispatch` → `normalizers` → `__init__`.

| # | File | LOC | Clean | Eff | Tests | Open findings | Status |
|---|---|---:|---:|---:|---|---|---|
| 1.1 | `constants.py` | 15 | 10 | 10 | n/a | none (fixed: `KN-7` part, `KN-13`, `KN-14`, `KN-15`; docstring reworded for options in `CR-11`) | **closed** |
| 1.2 | `errors.py` | 332 | 9 | 10 | ✓ | none (fixed: `KN-4`, `KN-9`, `KN-20` … `KN-29`; rewritten in `CR-11`) | **closed** |
| 1.2b | `rollover.py` *(new in `CR-11`)* | 212 | 9 | 10 | ✓ | none (fixed: `KN-30` … `KN-33`) | **closed** |
| 1.3 | `formatters.py` | 161 | 9 | 9 | ✓ | none (fixed: `KN-6`, `KN-7`, `KN-9`, `KN-11`, `KN-17`, `KN-42`, `KN-44`, `KN-45`, `KN-46`) | **closed** |
| 1.4 | `handlers.py` | 533 | 9 | 9 | ✓ | none (fixed: `KN-5`, `KN-7`, `KN-16`; `LabFileHandler` in `CR-11`, `KN-42`, `KN-43`, `KN-44`, `KN-46`, `KN-49`) | **closed** |
| 1.4b | `dispatch.py` | 318 | 9 | 10 | ✓ | none (fixed: `KN-18`, `KN-34`, `KN-36`, `KN-38`; `KN-19` by design, `KN-40`, `KN-44`, `KN-47`, `KN-48`, `KN-49`) | **closed** |
| 1.5 | `normalizers.py` | 101 | 10 | 10 | ✓ | none (fixed: `KN-2`, `KN-3`, `KN-7`, `KN-8`; one `normalize_name` in `CR-11`, `KN-42`, `KN-44`) | **closed** |
| 1.6 | `__init__.py` | 112 | 10 |  | n/a | none (fixed: `KN-41`) | **closed** |

Fixed before the pass: `KN-1`, `KN-10`, `KN-12` (and `CR-9`/`CR-10` landed in `handlers.py`).

### 2. core: closed

Order: `enums` → `specs` → `registry` → `builder` → `__init__`.

| # | File | LOC | Clean | Eff | Tests | Open findings | Status |
|---|---|---:|---:|---:|---|---|---|
| 2.1 | `enums.py` | 115 | 10 | 10 | ✓ | none (fixed: `CR-6`, `CR-20`) | **closed** |
| 2.1b | `specs.py` *(new in `CR-11`)* | 96 | 10 | 10 | ✓ | none (fixed: `CR-17`, `CR-19`, `CR-20`) | **closed** |
| 2.2 | `registry.py` | 155 | 10 | 10 | ✓ | none (fixed: `CR-3`, `CR-4`, `CR-18`, `CR-20`) | **closed** |
| 2.3 | `builder.py` | 736 | 9 | 9 | ✓ | none (fixed: `CR-7`, `CR-16`, `CR-17`, `CR-20`, `CR-21`, `CR-22`, `CR-23`) | **closed** |
| 2.4 | `__init__.py` | 29 | 10 |  | n/a | none | **closed** |

Fixed before the pass: `CR-1`, `CR-2`, `CR-5`, `CR-8`, `CR-9`, `CR-10`, `CR-11`.

### 3. Building blocks: closed

Order: `formats/__init__` → `features` (`detail` → `rotation` → `__init__`) →
`outputs` (`console` → `file` → `relay` → `__init__`) → `catalysts`
(`asynchronous` → `__init__`). Formats and features first, because the outputs
interpret them; catalysts last, because they wrap the built outputs. The old
`experiments/` package was removed in `CR-11`; its findings (`EX-1` … `EX-7`)
stay in the ledger, and `EX-7` moved with `RelayHandler` to `outputs/relay.py`.

| # | File | LOC | Clean | Eff | Tests | Open findings | Status |
|---|---|---:|---:|---:|---|---|---|
| 3.1 | `formats/__init__.py` | 20 | 10 | 10 | ✓ | none | **closed** |
| 3.2 | `features/detail.py` | 22 | 10 | 10 | ✓ | none (fixed: `EX-12`) | **closed** |
| 3.3 | `features/rotation.py` | 140 | 10 | 10 | ✓ | none (fixed: `EX-11`) | **closed** |
| 3.4 | `features/__init__.py` | 14 | 10 |  | n/a | none | **closed** |
| 3.5 | `outputs/console.py` | 107 | 10 | 10 | ✓ | none (fixed: `EX-10`, `EX-13`, `EX-14`) | **closed** |
| 3.6 | `outputs/file.py` | 108 | 10 | 10 | ✓ | none (fixed: `EX-11`, `EX-12`, `EX-13`) | **closed** |
| 3.7 | `outputs/relay.py` | 101 | 10 | 10 | ✓ | none (fixed: `EX-7`, `EX-10`, `EX-12`) | **closed** |
| 3.8 | `outputs/__init__.py` | 14 | 10 |  | n/a | none | **closed** |
| 3.9 | `catalysts/asynchronous.py` | 53 | 10 | 10 | ✓ | none (fixed: `EX-12`) | **closed** |
| 3.10 | `catalysts/__init__.py` | 12 | 10 |  | n/a | none | **closed** |

Fixed before the pass: `EX-1` … `EX-6` (in the files they were found in).

### 4. profiles: closed

Order: `observer` → `investigator` → `conspiracy_theorist` → `ai_agent` →
`gui` → `__init__`. (`base.py` and `build_profile` were removed in `CR-11`:
profiles are recipes.)

| # | File | LOC | Clean | Eff | Tests | Open findings | Status |
|---|---|---:|---:|---:|---|---|---|
| 4.1 | `observer.py` | 29 | 10 | 10 | ✓ | none (fixed: `PF-4`, `PF-5`, `PF-7`, `PF-8`) | **closed** |
| 4.2 | `investigator.py` | 30 | 10 | 10 | ✓ | none (fixed: `PF-4`, `PF-7`, `PF-8`) | **closed** |
| 4.3 | `conspiracy_theorist.py` | 34 | 10 | 10 | ✓ | none (fixed: `PF-4`, `PF-8`) | **closed** |
| 4.4 | `ai_agent.py` | 31 | 10 | 10 | ✓ | none (fixed: `PF-4`, `PF-7`, `PF-8`) | **closed** |
| 4.5 | `gui.py` | 45 | 10 | 10 | ✓ | none (fixed: `PF-6`, `PF-7`, `PF-8`) | **closed** |
| 4.6 | `__init__.py` | 34 | 10 |  | n/a | none (fixed: `PF-2`, `PF-3`, `PF-6`, `PF-7`) | **closed** |

Fixed before the pass: `PF-1`.

### 5. theories: closed

Order: `trace_exp` → `lifecycle_exp` → `throttle_exp` → `performance_exp` →
`process_exp` → `http_exp` → `sec_exp` → `db_exp` (the roadmap's rank order,
D-20) → `__init__`. The `_test_theory` harness was removed (`TH-4`). The eight idea files are reviewed
against the Idea stage format (Standards §3.4), not as working code.
(`async_exp.py` was removed when ASYNC was promoted, and `timed_file_exp.py`
when `TIMED_FILE` became the `TIMED` feature.)

| # | File | LOC | Clean | Eff | Tests | Open findings | Status |
|---|---|---:|---:|---:|---|---|---|
| 5.1 | `trace_exp.py` | 17 | 10 |  | n/a | none (fixed: `TH-3`, `TH-5`, `TH-6`) | **closed** |
| 5.2 | `lifecycle_exp.py` | 16 | 10 |  | n/a | none (fixed: `TH-6`) | **closed** |
| 5.3 | `throttle_exp.py` | 13 | 10 |  | n/a | none | **closed** |
| 5.4 | `performance_exp.py` | 12 | 10 |  | n/a | none (fixed: `TH-3`, `TH-5`, `TH-6`, `TH-7`) | **closed** |
| 5.5 | `process_exp.py` | 13 | 10 |  | n/a | none | **closed** |
| 5.6 | `http_exp.py` | 11 | 10 |  | n/a | none (fixed: `TH-3`, `TH-5`, `TH-6`) | **closed** |
| 5.7 | `sec_exp.py` | 10 | 10 |  | n/a | none (fixed: `TH-3`, `TH-6`, `TH-7`) | **closed** |
| 5.8 | `db_exp.py` | 11 | 10 |  | n/a | none (fixed: `TH-3`, `TH-6`, `TH-7`) | **closed** |
| 5.9 | `_test_theory.py` *(removed in `TH-4`)* | 0 |  |  | n/a | none (fixed: `TH-4`) | **closed** |
| 5.10 | `__init__.py` | 21 | 10 |  | n/a | none (fixed: `TH-7`) | **closed** |

Fixed before the pass: `TH-1`, `TH-2`.

### 6. Package root: closed

Order: `logger_lab/__init__.py` → `pyproject.toml` → `.gitignore`.

| # | File | LOC | Clean | Eff | Tests | Open findings | Status |
|---|---|---:|---:|---:|---|---|---|
| 6.1 | `logger_lab/__init__.py` | 80 | 10 | 10 | ✓ | none (fixed: `PK-10`, `PK-11`) | **closed** |
| 6.2 | ~~`main.py`~~ |  |  |  |  | deleted (`PK-4`) | **removed** |
| 6.3 | ~~`src/__init__.py`~~ |  |  |  |  | deleted (`PK-1`) | **removed** |
| 6.4 | `pyproject.toml` | 44 | 10 |  | n/a | none (fixed: `PK-5`, `PK-9`, `PK-12`) | **closed** |
| 6.5 | `.gitignore` | 17 | 10 |  | n/a | none (fixed: `PK-13`) | **closed** |

Fixed before the pass: `PK-2`, `PK-3`, `PK-6`, `PK-7`. (`PK-5`, the docs
shipping in the wheel, is listed on `pyproject.toml`. The docs moved to the
repository root, and the 2026-10-23 build has no `docs/` in the wheel or sdist.)

### 7. tests: closed

Order: `conftest` → `test_names` → `test_registry` → `test_composition` →
`test_levels` → `test_console` → `test_files` → `test_rotation` →
`test_sharing` → `test_threads` → `test_formatters` → `test_async` →
`test_relay` → `test_gui` → `helpers` (new in `TS-6`). Rewritten for the four kinds in `CR-11`
(`test_timed_file.py` became `test_rotation.py`).

| # | File | LOC | Tests | Clean | Covers | Open findings | Status |
|---|---|---:|---:|---:|---|---|---|
| 7.1 | `conftest.py` | 74 |  | 10 | Each test runs in `tmp_path`; handlers released afterwards; guards fail any test or run that logs inside the repo (`TS-3`) or leaks a shared file | none | **closed** |
| 7.2 | `test_names.py` | 90 | 17 | 10 | Every member of every kind by member, value and lower case; each block and profile builds; renamed members, other kinds' names and removed names rejected with the valid list; placeholders | none | **closed** |
| 7.3 | `test_registry.py` | 203 | 15 | 10 | Every member under its own key with the right spec type; the specs agree; every profile composes; typed lookup errors; the version matches `pyproject.toml`; `register_theory` checks; every idea names its kind; theories of each kind (feature with `on=` and options, output, catalyst group), `on=` refused where it can't apply, a format an output can't render | none (fixed: `TS-7`, `TS-9`) | **closed** |
| 7.4 | `test_composition.py` | 263 | 36 | 10 | Each profile's composition; one profile; profiles pin with `on=`; where features and formats go; nothing brings an output; what can't mix; options merge, unknown and bad values; the suggestion (most specific, caller's line, never adds or clashes); untouched-on-error; order | none (fixed: `TS-7`, `TS-9`) | **closed** |
| 7.5 | `test_levels.py` | 70 | 11 | 10 | Accepted and rejected levels (a custom name stays inside its test), entry points validate, INFO everywhere, `setLevel()` after build reaches every handler | none (fixed: `TS-7`, `TS-8`, `TS-9`) | **closed** |
| 7.6 | `test_console.py` *(new in `CR-11`)* | 95 | 11 | 10 | Rich on stderr, stdout for every format, text and Rich detail, JSON lines, brackets as text, bad format reported, markup per record | none (fixed: `TS-9`) | **closed** |
| 7.7 | `test_files.py` | 132 | 7 | 10 | Defaults, options on every profile's file, encoding/backups/max_bytes, detail on the file, JSON lines (also rotating), release and rebuild, Windows rotation, a log directory that can't be created (`LogDirectoryError`) | none (fixed: `TS-6`, `TS-7`, `TS-9`) | **closed** |
| 7.8 | `test_rotation.py` *(was `test_timed_file.py`)* | 351 | 47 | 10 | Period and boundary for every unit (every>1, `at=`, `day=`, new year, quarters); calendar anchoring; labels; `utc`; TIMED options normalized (strings, plurals, enums), every `Unit` and `Day` member by member and by string, and every bad value; dated, never-overwritten, size + time, numbered, retention, mtime period, monthly, idle period, oversized record; sharing, clash, `ASYNC` | none (fixed: `TS-7`, `TS-9`, `TS-10`) | **closed** |
| 7.9 | `test_sharing.py` | 160 | 11 | 10 | One handler per file across loggers, per-module levels and compositions, setup clashes leave nothing half-built, first-wins settings, foreign handlers untouched, sole-owner rebuild, last-release close, no reopen after close | none (fixed: `TS-6`, `TS-9`) | **closed** |
| 7.10 | `test_threads.py` | 106 | 4 | 10 | Concurrent builds, 8-thread rotation without losing a line (plain and `ASYNC`), rebuilding mid-traffic | none (fixed: `TS-6`, `TS-9`) | **closed** |
| 7.11 | `test_formatters.py` | 166 | 9 | 10 | JSON v1.2 fields with the text timestamp, exceptions and stack (also through `ASYNC`), `log_event` extra and caller source, non-serializable fallback, text layouts | none (fixed: `TS-7`) | **closed** |
| 7.12 | `test_async.py` | 268 | 13 | 10 | One handler and the worker writes, a record is final when logged, order, one worker, nothing built to wrap, failing output, release writes the queue, release and exit within `DRAIN_TIMEOUT`, drain from the worker, restart, two workers never coexist, a bad format call | none (fixed: `TS-6`, `TS-7`, `TS-9`) | **closed** |
| 7.13 | `test_relay.py` | 110 | 6 | 10 | One relay that hands over the record, per-subscriber level, none = no handler, failing callback, the echo guard (sync and `ASYNC`) | none (fixed: `TS-9`) | **closed** |
| 7.14 | `test_gui.py` | 79 | 3 | 10 | Shape (with and without subscribers), LabFrame-style child propagation off-thread with no stdout, many job threads in order | none (fixed: `TS-9`) | **closed** |
| 7.15 | `helpers.py` *(new in `TS-6`)* | 40 |  | 10 | Shared helpers: threads that start together, the lines a rotating file wrote, a logger's one file handler | none | **closed** |

Suite-level: `TS-2` (coverage gaps) fixed. Fixed before the pass: `TS-1`,
`TS-3`, `TS-4`.

### 8. README + docs: closed

Order: `README.md` → `API_Reference.md` → `Standards_and_Tracker.md` →
`Continuation.md` → `Framework_Comparison.md` → `Cleanliness_Tracker.md`
(last, so it records the pass itself).

| # | File | LOC | Clean | Open findings | Status |
|---|---|---:|---:|---|---|
| 8.1 | `README.md` | 637 | 10 | none (fixed: `DOC-5`, `DOC-6`, `DOC-7`, `DOC-8`, `DOC-9`) | **closed** |
| 8.2 | `docs/API_Reference.md` (repo root) | 422 | 10 | none (fixed: `DOC-5`, `DOC-7`) | **closed** |
| 8.3 | `docs/Standards_and_Tracker.md` | 428 | 10 | none (fixed: `DOC-5`, `DOC-6`, `DOC-9`) | **closed** |
| 8.4 | `docs/Continuation.md` | 305 | 10 | none (fixed: `DOC-4`, `DOC-5`, `DOC-6`, `DOC-9`) | **closed** |
| 8.5 | `docs/Framework_Comparison.md` | 97 | 10 | none (fixed: `DOC-6`, `DOC-7`) | **closed** |
| 8.5b | `docs/Feedback_Guide.md` | 282 | 10 | none (fixed: `DOC-6`) | **closed** |
| 8.6 | `docs/Cleanliness_Tracker.md` | 478 | 10 | none | **closed** |

Fixed before the pass: `DOC-1`, `DOC-2`. (`PK-5`, whether these docs ship in
the wheel, is decided in pass 6.)

---

## Findings ledger (Round 1)

| ID | Type | File | Finding | Decision | Status |
|---|---|---|---|---|---|
| DOC-4 | Doc bug | `Continuation.md` | D-17 reads "it stays **0.2.0** (unpublished), not 0.2.0". The decision was "not 0.3.0". A find-and-replace of 0.3.0 → 0.2.0 turned it into a contradiction (the original wording is in the 2026-10-22 session). | **Done:** "not 0.3.0". | fixed |
| DOC-5 | Doc drift (`CR-18`) | `Standards_and_Tracker.md`, `Continuation.md`, `API_Reference.md`, `README.md` | Four claims outlived the plain registry tables. Standards §2.3 says "the registry plans every profile at import". Continuation lists "`register_*` for every kind" as new in 0.2.0, and its promotion rule says to register with "that kind's `register_*`". The API Reference and README describe `RegistrationError` as a broken "profile recipe". | **Done:** Standards §2.3 says the tests plan every profile. Continuation lists `register_theory()` and promotes into its kind's table in `core/registry.py`. `RegistrationError` reads "a malformed theory spec, or a lookup that finds nothing" in the API Reference and README. | fixed |
| DOC-6 | Doc drift (this round) | every doc | What passes 1 to 7 changed hasn't reached the docs. **Continuation:** the theory kinds in §3 contradict the idea files (`TH-6`). Phase 4 still says "resume the cleanliness passes (the harness's tests)". §6 still says to review the redesign and add the `EX-7` guard. The 0.2.0 change list lacks `__version__`, `rich>=12.6.0` and the removed `_test_theory` harness (all in 0.1.1). **Standards:** the §5 tracker says the passes are "Paused" and pass 3 "pending". §6 is the old priority. §4 says pyrefly suppresses 11 errors, but it is 10. **README and Feedback Guide:** the tree misses `Unit`, `Day`, `value_of` and `__version__`, and two places say `RichHandler` where it is `LabRichHandler`. Both still say windowed builds have no *stdout* (`PF-6` fixed this in `gui.py` only). **Framework Comparison:** it says "112 tests", says the gaps are "led by promoting time rotation" (done), and lists `PERFORMANCE` twice in its order. The snapshot dates say 2026-10-22. | **Done:** Continuation's theory kinds follow the idea files. Phase 4 no longer resumes the passes, and §6 is the next real step. The change list adds `__version__`, `rich>=12.6.0` and the removed harness, and a row records round 1. Standards' tracker, §6 and pyrefly baseline (10 suppressed, from six comments) are current. The README tree has `Unit`, `Day`, `value_of()`, `__version__` and `LabRichHandler`, and the Feedback Guide says `LabRichHandler`. Both say stdout or stderr. The comparison says 190 tests, drops the time-rotation gap, and lists `PERFORMANCE` once. The snapshot dates read 2026-10-23. | fixed |
| DOC-7 | Accuracy | `API_Reference.md`, `README.md`, `Framework_Comparison.md` | `with_level` "sets the logger's level (and the console handler's)". Since `EX-9` the handlers are `NOTSET`. The `JSONFormatter` row says "v1.1 only adds fields to v1", but v1.2 changed the timestamp. The README's `observer` row promises `LEVEL: message`, while Rich prints a level column. Its `conspiracy_theorist` example passes `exc_info=True` outside an `except`, so the file gets "NoneType: None". The new-profile example passes `ProfileSpec` its fields by position (`PF-8`). `with_format` shows no `**options`, unlike the code. The exception paragraph sits alone between two rules, outside the JSON section. The comparison says `show_path` is hard-coded, but `VERBOSE` sets it. | **Done:** `with_level` is "the one switch: every handler is `NOTSET`". The JSON row gives v1.1's and v1.2's changes. `observer` shows "level and message only". The archival example logs inside `except` with `logger.exception`. `ProfileSpec` uses keywords, and `with_format` shows `**options`. The exception paragraph joined the JSON section. The comparison says `show_path` follows `VERBOSE`. | fixed |
| DOC-8 | Owner's call | `README.md` | The Status says "STABLE RELEASE: `v0.2.0`". 0.2.0 isn't published, the next line says "still in active development", and the Development Status classifier was dropped. The roadmap also lists "AI-assisted debugging tools" and "Distributed tracing support", which aren't in the `D-20` roadmap. | Owner, 2026-10-23: as recommended. **Done:** "Current version: `0.2.0`", and the roadmap mirrors `D-20` (publish, then `TRACE` with `LIFECYCLE`, `THROTTLE`, `PERFORMANCE`, `PROCESS`, the specialized theories, then configuration). | fixed |
| DOC-9 | Consistency | `README.md`, `Standards_and_Tracker.md`, `Continuation.md` | Some README prose lines run to 130 characters while the rest wrap near 95, and two Standards lines from `PF-6` and `TH-6` came out long. Continuation's decision table is out of order (D-1, D-2, D-3, D-7, D-9, …). | **Done:** no prose line over 100 characters outside tables and code, and the decision table runs D-1 to D-27. | fixed |
| TS-6 | Duplication | `test_async.py`, `test_threads.py`, `test_files.py`, `test_sharing.py` | The 8-thread rotating-file test exists twice, once plain (`test_threads`) and once behind `ASYNC` (`test_async`). Each copy has its own `THREADS`, `RECORDS`, `LINE`, thread start-up and line reading. `test_async` also starts threads by hand twice, where `test_threads` has `run_together`. `file_handler()` is written twice, in `test_files` and `test_sharing`, and the two versions differ. | **Done:** one rotating-file test in `test_threads`, parametrized over plain and `ASYNC` (the `ASYNC` copy now also checks it really rotated). `tests/helpers.py` holds `run_together`, `written_lines` and `file_handler`, and `test_async` uses `run_together` too. pyrefly's `search-path` includes `tests/`, as pytest does. | fixed |
| TS-7 | Consistency | `test_registry.py`, `test_levels.py`, `test_formatters.py`, `test_composition.py`, `test_rotation.py`, `test_async.py` | A banner still says the tables were "once checked at import". The `LogDirectoryError` test is about the file output but lives in `test_levels`. `test_formatters` imports `drain` and `lab` inside a test. `test_composition` compares `planned.output.value`, the `CR-23` pattern PyCharm flags. One banner's edges don't line up. `test_async` replaces `console.emit` by assignment instead of `monkeypatch`. | **Done:** the banner reads "The built-in tables", the directory test is in `test_files`, `drain` and `lab` are imported at the top, `planned.output is Output.FILE`, the banner edges match, and `monkeypatch.setattr(console, "emit", ...)`. | fixed |
| TS-8 | Isolation | `test_levels.py` | `test_accepted_levels` calls `logging.addLevelName(25, "NOTICE")` and never undoes it. Every later test in the run sees level 25 named "NOTICE", so the result can depend on test order. | **Done:** the test swaps in copies of logging's two level tables with `monkeypatch`, so "NOTICE" is gone when it ends. Shown with a probe test run after it: level 25 kept the name before the fix, and not after. | fixed |
| TS-9 | Consistency | 12 test files | 28 lines are over 120 characters. Two callbacks take a `record` they never use (`bad`, `broken`), which PyCharm flags. `test_threads` catches `BaseException` with no `noinspection` comment. | **Done:** no line over 120. `_record` for the unused parameters. `# noinspection PyBroadException` with a reason on the `BaseException` catch. | fixed |
| TS-10 | Coverage | `test_rotation.py` | Standards §4 pins every enum member, by member and by value string. `Unit` and `Day` are only partly covered: 3 of their 12 members are passed as members. | **Done:** `test_every_unit_and_day_works_as_a_member_or_a_string`. With `"sunday"` made unresolvable, it fails and every other test passes. | fixed |
| PK-9 | Packaging | `pyproject.toml` (`readme`), `README.md` | The README is the PyPI project page. Its one link into `docs/` (`docs/Feedback_Guide.md`) is relative, so on PyPI it would 404: `docs/` is in neither the wheel nor the sdist (checked with `uv build`). | **Done:** the link points at the Feedback Guide on GitHub (`main`), so it works on PyPI once the docs are merged. | fixed |
| PK-10 | API | `logger_lab/__init__.py` | No `__version__`. Most packages have one, and bug reports ask for it. | **Done:** `__version__ = importlib.metadata.version("logger-lab")`, with an API Reference row. `test_the_version_is_the_one_in_pyproject`, shown to fail with a hard-coded version. | fixed |
| PK-11 | Doc | `logger_lab/__init__.py` | The docstring example assigns `logger` twice, so the second line reads as a replacement for the first. | **Done:** two named loggers (`logger`, `nightly`), each with a comment. The docstring also mentions `__version__`. | fixed |
| PK-12 | Packaging | `pyproject.toml` | `rich>=15.0.0` is just the version in the lock file. It would refuse any project pinned to Rich 12 to 14. The suite passes on Rich 12.6.0, 13.0.0, 13.9.4 and 14.0.0 (Python 3.10; the imported version was checked). | **Done:** `rich>=12.6.0`, and `uv.lock` updated (it still installs 15.0.0). The full suite passes on Rich 12.6.0 with Python 3.10. | fixed |
| PK-13 | Repo (owner) | `.gitignore`, `.idea/` | Seven `.idea` files are tracked, and `.gitignore` says shared settings "stay tracked". The standing rule is never to commit `.idea`, so `logger-lab.iml` and `misc.xml` show as modified in every status. | Owner, 2026-10-23: (a), ignore `.idea/` entirely. **Done:** `.gitignore` ignores `.idea/`, with a comment saying why. **At the next commit:** `git rm -r --cached .idea` untracks the seven files. They stay on disk. | fixed |
| TH-4 | Usability | `theories/_test_theory.py` | A placeholder is "the expected result", yet the harness ends in a full traceback for it. A typo in the profile does the same. Nothing tests the harness, though the Trial stage depends on it. Its docstring doesn't say that the profile's file lands in `logs/app.log` where it runs (ignored by git). | Owner, 2026-10-23: a theory is tried by adding it to a builder, so the harness isn't needed. **Done:** `_test_theory.py` removed. The README, API Reference, Standards §3.4 and Framework Comparison now say to try a registered theory with `with_theory()` in a test. Two stale steps in the API Reference went with it ("at the bottom of `registry.py`", "that kind's `register_*`"). | fixed |
| TH-5 | Doc drift | `theories/trace_exp.py`, `http_exp.py`, `performance_exp.py` | The idea docstrings lag the roadmap (`D-20`, Continuation). `TRACE` leaves out the measured constraint: context must be stamped on the caller's thread, because a filter on an output runs on the dispatch worker and sees none. `HTTP` reads `TRACE` context, so it shares the constraint. `PERFORMANCE` logs through `log_event`, where the roadmap emits lifecycle events and depends on `LIFECYCLE`. | **Done:** `TRACE` states the measured caller-thread constraint and the `copy_context()` note. `HTTP` says the constraint applies to it. `PERFORMANCE` emits lifecycle events and names its dependencies. | fixed |
| TH-6 | Design (owner) | `theories/*_exp.py` | Theories are "building blocks of any of the four kinds", but six ideas don't say which kind. Two aren't one: `LIFECYCLE` is a helper on `log_event`, and `PERFORMANCE` a decorator. Neither could be selected with `with_theory()`. | Owner, 2026-10-23: agreed. **Done:** every idea has a `Kind:` line and its roadmap rank. `LIFECYCLE`, `PERFORMANCE` and `DB` say "helper". Standards §3.4 has a Helpers paragraph: never registered, tried in tests, promoted into the public API beside `log_event`. `test_every_theory_has_an_idea_file_that_names_its_kind`, shown to fail without a `Kind:` line. | fixed |
| TH-7 | Consistency | `theories/__init__.py`, `db_exp.py`, `performance_exp.py`, `sec_exp.py` | Four sentences have two spaces after the period, and `__init__`'s docstring line is 121 characters. The `__init__` docstring is two lines, with no list of the ideas or their order. | **Done:** single spaces, no line over 120, and `__init__` lists the eight ideas in roadmap order with their kinds. | fixed |
| PF-5 | Doc bug | `profiles/observer.py` | The example logs `"Disk usage above 90 %%"` with no arguments. Logging only applies `%` when there are arguments, so it prints `90 %%`, not the `90 %` the comment promises. | **Done:** the example logs `"Disk usage above 90%"` with no arguments, so no escaping is needed. Its comment shows the Rich line as it really prints (`WARNING  Disk usage above 90%`), run to confirm. | fixed |
| PF-6 | Doc | `profiles/__init__.py`, `profiles/gui.py` | `__init__` still says "the registry plans each one at import time". Since `CR-18`, the tests do. `gui` says windowed builds have no *stdout*. Under `pythonw` both `sys.stdout` and `sys.stderr` are `None`, and the console writes to stderr by default. (A console added there drops records quietly; it doesn't raise.) | **Done:** `__init__` says the tests plan every profile. `gui` names both streams and says a console there would drop every record. The same stale "planned at import" claim was also fixed in the README tree, `Framework_Comparison.md`, Standards §2 rule 9 and its tracker row, and `RegistrationError`'s docstring. | fixed |
| PF-7 | Consistency | `profiles/__init__.py`, `investigator.py`, `observer.py`, `ai_agent.py`, `gui.py` | Four sentences have two spaces after the period. `__init__` aligns its imports into columns (PyCharm: "multiple spaces before keyword"), one table row is out of line, and the table's order differs from `PROFILE_SPECS`. | **Done:** single spaces, plain imports, and the table in `PROFILE_SPECS` order with its columns aligned. | fixed |
| PF-8 | Readability | every profile | `ProfileSpec(ProfileType.GUI, gui, "...")` is positional, while every building-block spec names its fields (`OutputSpec(member=...)`). A reader has to know the order. | **Done:** every `ProfileSpec` names `member=`, `recipe=` and `summary=`. | fixed |
| EX-10 | Consistency | `outputs/console.py`, `outputs/relay.py` | Broad `except Exception` in `LabRichHandler.emit` and `RelayHandler.emit`, the `KN-48` pattern PyCharm flags. Catching everything is right there: a handler must never raise into the caller. | **Done:** `# noinspection PyBroadException` on both, each `except` saying why (a logging call must never raise). | fixed |
| EX-11 | Consistency | `outputs/file.py`, `features/rotation.py` | Five f-strings and comparisons use `.value` on an enum, which PyCharm types as a function ("FunctionType string value might not be useful", as `CR-23`). | **Done:** `value_of()` moved to `core/enums.py`, and `file.py`, `rotation.py` and `builder.py` all import it from there. No `.value` is left in the building blocks. | fixed |
| EX-12 | Consistency | `outputs/file.py`, `outputs/relay.py`, `catalysts/asynchronous.py`, `features/detail.py` | Three lines over 120 characters (`file.py:25`, `file.py:85`, `relay.py:37`). Four sentences have two spaces after the period. `DETAIL_OUTPUTS` and `DETAIL_FORMATS` have no comment. | **Done:** no line over 120, single spaces after periods, and both detail constants say what they are. | fixed |
| EX-13 | Readability | `outputs/console.py`, `outputs/file.py` | `build_console` picks a `stream` even for Rich, which never uses it. `check_file` calls a set of features `rotating`, the name `build_file` uses for ROTATING's options. `build_file`'s settings dict packs four conditionals into one expression. | **Done:** the stream is picked only for `StreamHandler`. `check_file` says `rotations`. `build_file` builds the kind and settings one rule at a time, and `open_handler` is a named function. `test_a_file_shares_by_its_whole_setup` pins the kind and settings with both rotations, and fails when any part is dropped. | fixed |
| EX-14 | Doc | `outputs/console.py` | A `TEXT` or `JSON` console binds `sys.stderr` (or `sys.stdout`) when it is built, as `StreamHandler` does. A Rich console looks it up on every record. So replacing `sys.stderr` later reaches Rich only. | **Done:** the console's module docstring says which console follows a replaced `sys.stderr`. | fixed |
| CR-23 | Consistency | `core/builder.py` | PyCharm (owner, 2026-10-23): "expected `dict[str, Any]`, got `dict[() -> Any …]`", "expected `Iterable[SupportsRichComparisonT]`, got `Generator[() -> Any …]`", and "'FunctionType' string value might not be useful". PyCharm can't type `.value` on a union of enums. Also "member 'None' … has no attribute 'value'" on the format check, and "'FormatSpec' has no attribute 'check'" after `spec_of()`. | **Done (2.3):** a typed `value_of(member) -> str` replaces `.value` throughout; the format check reads `target.format` into a local; `spec_of(member, FeatureSpec)` returns the type it was asked for, replacing the `assert isinstance` lines. Second round (PyCharm, 2026-10-23): `value_of` itself tripped "FunctionType", so it reads the value with `getattr` (a typed `Enum` base was tried, and pyrefly rejects overriding `Enum.value`). The format check nests its two conditions, so the `None` narrowing holds. `spec_of` returns `cast(SpecT, spec)` after its runtime check, since PyCharm doesn't narrow through a TypeVar. | fixed |
| CR-16 | Correctness | `core/builder.py` | `ProfileSuggestionWarning` uses a fixed `stacklevel=4`. That is right through `build()`, but through a direct `plan()` it points at the caller's caller (verified: line 9 instead of line 5). | **Done (2.3):** `caller_stacklevel()` walks the stack to the first frame outside `logger_lab`. `test_the_suggestion_points_at_the_callers_line_through_plan_too`, shown to fail without it. | fixed |
| CR-17 | Correctness | `core/specs.py`, `core/builder.py` | An output's `formats` is only used to check its default format. The builder never checks a format against the output, so a format theory that fits the console plans fine and would be rendered silently as TEXT (verified). Two sources of truth: `FormatSpec.fits` and `OutputSpec.formats`. | **Done (2.3):** `finish_output` raises "the console output can't render the 'SEC' format". A test pins that a format fits exactly the outputs that render it. `test_an_output_refuses_a_format_it_cannot_render`, shown to fail without it. | fixed |
| CR-18 | Consistency | `core/registry.py` | The registration imports sit at the bottom of the module (PyCharm: PEP 8 E402), and the loop variables `_spec` and `_profile` leak into the module with an unexplained `_`. `LabError` is imported lazily though `errors` is already imported at the top. `get_profile` raises a bare `KeyError`, unlike the other lookups. | Owner, 2026-10-23: plain tables. **Done (2.2):** the registry imports every spec at the top and writes the tables out. `register_output` … `register_profile`, `check_spec` and `check_profiles` are gone; their checks became tests (`test_every_member_has_a_spec_of_its_kind_under_its_own_key`, `test_the_specs_agree_with_each_other`, `test_every_profile_composes`). `register_theory` keeps its check. `get_profile` raises `RegistrationError`. This also cleared PyCharm's "unresolved attribute 'member' for class 'type'". | fixed |
| CR-19 | Consistency | `core/specs.py` | `from typing import Callable, Mapping`: deprecated aliases (as `KN-43`). | **Done (2.1b):** `collections.abc`. | fixed |
| CR-20 | Consistency | `builder.py`, `registry.py`, `specs.py`, `enums.py` | Style nits. Four banners have mismatched edges or extra padding. `spec_of` runs to 130 characters. Nine sentences have two spaces after the period. The registry tables line up their colons (`OUTPUTS   : dict`, PEP 8 E203). `KIND_ENUMS` and `KIND_SPECS` have no comment. `lab()`'s docstring puts Example before Returns. | **Done:** banners aligned, no line over 120, single spaces, no aligned colons, `lab()`'s docstring in order. | fixed |
| CR-21 | Readability | `core/builder.py` | Three helpers have untyped parameters: `merged_options(spec, ...)`, `attach_targets(member, ...)` and `merge(table: dict, key: object, ...)`. | **Done (2.3):** full type hints, and `spec_of(member, spec_type)` returns the spec type it was asked for. | fixed |
| CR-22 | Efficiency | `core/builder.py` | A `plan()` without a profile and with two or more outputs runs every profile's recipe again (`profile_blocks()`), and error messages do too (`profile_with`). It is setup time only, a few microseconds. | **Done (2.3):** noted in `suggest_profile`'s docstring; nothing is cached. | fixed |
| KN-48 | Consistency | `logging_kernel/dispatch.py` | PyCharm: "too broad exception clause" (owner, 2026-10-23). A logging handler must never raise into the caller, so catching everything is the point where it happens. | **Done (1.4b):** the worker's outer `except` was redundant (`deliver` guards each target), so it is now `try`/`finally`. The two that remain, in `emit` and `deliver`, carry `# noinspection PyBroadException` and say why. `outputs/console.py` and `outputs/relay.py` have the same pattern, for pass 3. | fixed |
| KN-49 | Consistency | `dispatch.py`, `handlers.py` | PyCharm: "member of None" on `worker.start()` and `self.stream` (owner, 2026-10-23). PyCharm can't narrow a module global or an attribute that may be `None`. | **Done:** the new value goes into a local first (`started.start()`, then `worker = started`; `stream = self.stream` before use). Stop markers are a small `Stop` dataclass instead of a bare `int`, which reads more plainly. | fixed |
| KN-40 | Bug | `logging_kernel/dispatch.py` | On an `ASYNC` logger, a bad format call (`logger.info("%d", "x")`) raises `TypeError` out of the logging call and crashes the caller (verified 2026-10-23). `AsyncHandler.emit` merges the message (`freeze`) with nothing around it. The `gui` profile is affected. | **Done (1.4b):** `emit` guards the merge and reports it through `handleError`. `test_a_bad_format_call_on_an_async_logger_is_reported_not_raised`, shown to fail without it. | fixed |
| KN-41 | Doc | `logging_kernel/__init__.py` | The API Reference lists `DRAIN_TIMEOUT` under `logger_lab.logging_kernel`, but it isn't exported there, and setting a copy there wouldn't change anything. It lives in `logging_kernel.dispatch`. | **Done (1.6):** the API Reference says it lives in, and is set on, `logger_lab.logging_kernel.dispatch`. | fixed |
| KN-42 | Consistency | `formatters.py`, `handlers.py`, `normalizers.py` | Section banners are single comment lines (`# Handler guard`, `# JSONFormatter`), and in `normalizers.py` they are examples (`# Output.FILE, "file" or "FILE"`). Standards §1.4 uses boxed banners, like `errors.py` and `dispatch.py`. | **Done:** every section in the package has a boxed banner with matching edges. | fixed |
| KN-43 | Consistency | `logging_kernel/handlers.py` | `from typing import Callable, Iterable` are deprecated aliases (the `KN-25` follow-up). | **Done (1.4):** `collections.abc.Callable` and `Iterable`. | fixed |
| KN-44 | Consistency | `formatters.py`, `handlers.py`, `dispatch.py`, `normalizers.py` | Small style nits. Two signatures put the closing parenthesis on its own indented line (`log_event`, `configure_handler`). Two lines run past 120 characters, PyCharm's limit (`dispatch.py:42`, `handlers.py:266`). Ten sentences have two spaces after the period. `AsyncHandler` says "``async`` logger". | **Done:** one-line signatures, no line over 120 characters, single spaces after periods, ``ASYNC`` in the docstring. | fixed |
| KN-45 | Doc | `logging_kernel/formatters.py` | Comments that restate the code in `JSONFormatter.format` (`# A log entry`, `# Adds the extras to the entry`), and a heading comment above the method. | **Done (1.3):** removed. `format` reads top to bottom without them. | fixed |
| KN-46 | Efficiency | `formatters.py`, `handlers.py` | `JSONFormatter` re-renders the traceback for every handler that formats the record, where `logging.Formatter` caches it in `record.exc_text`. Separately, `ROTATING` formats each record twice, once to measure and once to write (the stdlib does the same). | **Done (1.3):** the traceback is cached in `record.exc_text`, as `logging.Formatter` does. The double format under `ROTATING` stays, like the stdlib's. `test_a_traceback_is_rendered_once_however_many_formatters_see_it`, shown to fail without the cache. | fixed |
| KN-47 | Correctness | `logging_kernel/dispatch.py` | If `stop_worker()` runs while another thread is logging, a record can land behind the stop marker. It then waits for the next record to start a worker. It can't happen at exit, only with a manual `stop_worker()` during traffic. | **Done (1.4b):** documented in `stop_worker`'s docstring, as a note. | fixed |
| KN-38 | Bug | `logging_kernel/dispatch.py` | After `stop_worker()` times out (its worker stuck in a subscriber) and logging goes on, a second worker starts beside the stuck one. Both then deliver, so order across them isn't guaranteed (verified 2026-10-23). It can't happen at exit, only when `stop_worker()` is called by hand. | Owner, 2026-10-23: fix with a generation number. **Done:** each worker is started with a generation; a stop marker names the generation it stops, so a newer worker skips an older one's marker; a worker replaced while stuck finishes its record and exits. `drain()` and `close()` recognize any worker thread, stale ones included. `test_a_timed_out_stop_never_leaves_two_workers_or_a_lost_record`, shown to fail without either half. | fixed |
| CR-13 | Consistency | `core/builder.py` | `with_theory(theory, on=...)` silently ignores `on=` for an output or catalyst theory. | Owner, 2026-10-23: raise. **Done:** `with_theory(on=...)` raises `CompositionError` for an output or catalyst theory. `test_on_is_refused_for_a_theory_that_cannot_use_it`. | fixed |
| CR-14 | Dead | `core/specs.py` | `OutputPlan.level` is no longer used by any built-in output (handlers are `NOTSET` since `EX-9`). | Owner, 2026-10-23: remove it if not needed. **Done:** removed from `OutputPlan` and both places that built one; nothing read it. | fixed |
| KN-39 | Doc | `logging_kernel/handlers.py` | `ROTATING`'s `max_bytes` counts characters, not bytes, like the stdlib. So the cap is approximate for non-ASCII text or UTF-16. | Owner, 2026-10-23: count encoded bytes. **Done:** `LabFileHandler.encoded_size()` counts the line in the file's encoding, with `os.linesep` newlines, minus the byte-order mark UTF-16 adds to every encode. `test_max_bytes_caps_bytes_not_characters` (UTF-8 and UTF-16), shown to fail without it. | fixed |
| CR-15 | Design | `core/builder.py` | There is no way to take a feature or format away from a profile (say, `conspiracy_theorist` with a minimal console). The user must compose by hand. | Owner, 2026-10-23: by design. Profiles are preconfigured for a reason; to change one, compose by hand. | by design |
| KN-36 | Bug | `logging_kernel/dispatch.py`, `outputs/relay.py` | Exit could hang on a stuck subscriber. `AsyncHandler.close()` drained with no timeout (12 s for a 12 s subscriber, forever for one that never returns), and waited for *every* logger's queue. `logging.shutdown()` also takes each handler's lock, which the stdlib `handle()` held for as long as a subscriber ran. | Owner, 2026-10-23: fix. **Done:** each `AsyncHandler` counts its own queued records and waits for them at most `DRAIN_TIMEOUT` (renamed from `EXIT_DRAIN_TIMEOUT`); `stop_worker()` keeps one deadline for drain and join; `RelayHandler` serializes calls with its own re-entrant lock, outside the handler lock. A 30 s stuck subscriber now delays exit by 5 s. Two tests (release, and exit in a subprocess), each shown to fail without its fix. | fixed |
| CR-12 | Bug | `core/builder.py` | `ProfileSuggestionWarning` ignored `on=`. A minimal console beside a verbose file was told to use `conspiracy_theorist`, which then raised a `CompositionError`. With VERBOSE on the file only, it would have added VERBOSE to the console. | Owner, 2026-10-23: fix. **Done:** the hand-made composition is replayed on each candidate profile (`LabBuilder.replayed_on`); only a profile that plans to exactly the same composition is suggested. Shown to fail without the check. | fixed |
| KN-37 | Design | `logging_kernel/formatters.py` | JSON timestamps were UTC ISO-8601 with microseconds, text ones local and to the second. | Owner, 2026-10-23: the same format. **Done:** JSON uses `DATE_FORMAT`, local time; the schema is now Mosquito Lab Logging Standard v1.2 (a breaking change for `timestamp` only). The JSON timestamp carries no timezone; the owner will add one only if a real gap shows up (2026-10-23). | fixed |
| TS-5 | Test | `tests/` | 316 tests, many of them one behavior multiplied by parametrize (83 for names alone). | Owner, 2026-10-23: keep the relevant tests and the edge cases. **Done:** 181 tests. Lists are looped inside one test; TIMED's option checks moved to `test_rotation.py`; trivial tests dropped (a handler's stream object, per-path sharing); Rich internals (`_log_render`) no longer read. Every bug fix's test re-checked to fail without its fix. Found on the way: without the EX-7 guard a self-logging subscriber deadlocked on the relay lock, so it became re-entrant. | fixed |
| EX-8 | Bug | `outputs/console.py` | The Rich console had `markup=True`, so `logger.info("scanning [/usr/bin]")` raised `MarkupError` out of the logging call and crashed the caller. `RichHandler` also formats outside its own `try`, so `logger.info("%d", "x")` raised too. Both predate `CR-11`. Found in the 2026-10-23 sweep. | **Done 2026-10-23:** `markup=False` (styling per record with `extra={"markup": True}`), and `LabRichHandler` reports any failure through `handleError`. Three tests, each shown to fail without its fix. | fixed |
| EX-9 | Bug | `outputs/console.py` | The console handler kept the level from build time, so `logger.setLevel(DEBUG)` after the build reached the file but not the console. | **Done 2026-10-23:** the console handler is `NOTSET` like the file. `test_handlers_have_no_level_so_the_logger_level_is_the_one_switch`. | fixed |
| KN-34 | Bug | `logging_kernel/dispatch.py` | `AsyncHandler.deliver` had no guard per target. When one output raised, the outputs after it lost the record. | **Done 2026-10-23:** each target is guarded and reported through its own `handleError`. `test_a_failing_output_does_not_cost_the_others_the_record`. | fixed |
| KN-35 | Bug | `logging_kernel/handlers.py` | `LabFileHandler` rotated empty files. An idle period left a 0-byte timed backup that counted against `backup_count`. A record bigger than `max_bytes` rotated an empty file too (the stdlib guards this from 3.13, gh-116263). | **Done 2026-10-23:** an idle period moves on without a backup, and the size rule never rotates an empty file. Two tests. | fixed |
| PK-8 | Consistency | `pyproject.toml` | The description still said "Custom loggers to make debugging easy" (roadmap 2.3), and there was no license, author, URL or classifier metadata. | **Done 2026-10-23:** a feedback description, `license = "MIT"` with `license-files`, authors, project URLs, keywords and classifiers (no Development Status, owner 2026-10-23, so it can't contradict the README's release line). Checked in the built wheel's metadata. The only version classifier is `Programming Language :: Python :: 3`, with `requires-python >= 3.10` (owner, 2026-10-23). 3.10, 3.13 and 3.14 tested. | fixed |
| KN-33 | Design | `logging_kernel/rollover.py`, `features/rotation.py` | `TIMED` mixed periods and weekdays in one `every=` value, and couldn't express "every 6 hours", "half past each hour" or "every other Monday". | Owner, 2026-10-23 (Continuation D-27): the `schedule` package's options as keyword arguments, `every=`, `unit=`, `day=`, `at=` and `utc=`. Periods are anchored to the calendar, and `month` stays. `unit=` and `day=` take the new `Unit` and `Day` enums or their names, and `every` defaults to 1 (owner, 2026-10-23). **Done:** `TimeRule(every, unit, day, at, utc)`, `check_timed` and `parse_at(value, unit)` rewritten; 308 tests (period and boundary cases for every unit, calendar anchoring, option normalization, every bad value). README, API Reference, Continuation, Standards and Framework Comparison updated. | fixed |
| DOC-3 | Consistency | every file | The owner's writing rule (2026-10-23, Standards §1.4): short sentences joined with periods, no em dashes. About 460 em dashes and a dozen long sentences were spread over 55 files. Docstrings still had pre-`CR-11` words (experiment, channel, factory), two had the summary on the `"""` line, and some used Sphinx roles. British spellings remained (`labelled`, `behaviour`, `specialised`). | **Done 2026-10-23:** every file in `src/`, `tests/`, the README and `docs/` rewritten. Only the rule itself still shows the character. No sentence over 30 words remains outside code examples and list cells. `roll_labelled`/`prune_labelled` became `roll_labeled`/`prune_labeled`. Empty table cells read "none" or "n/a", and unscored cells are blank. | fixed |
| KN-30 | Bug | `logging_kernel/rollover.py` | An out-of-range `at=` (`"25:00"`, `"7:60"`) surfaced as the stdlib's message, `'TIMED' hour must be in 0..23`, without naming `at=`. | **Done (1.2b):** `parse_at` checks the range: `at='25:00' is not a time of day (00:00 to 23:59)`. Two tests added. | fixed |
| KN-31 | Doc | `logging_kernel/rollover.py` | The module docstring claimed "every day at 02:00" stays at 02:00 across DST changes. An `at=` inside the skipped spring hour rolls over an hour late that day (PEP 495). It can't be checked on this machine, whose zone has no DST. | **Done (1.2b):** the exception is stated, with `utc=True` as the way around it. | fixed |
| KN-32 | Consistency | `logging_kernel/rollover.py` | Em dashes, a long sentence, `start_time`'s docstring leaving out weekdays, `ValueError` without backticks, and `WEEKDAYS`/`MIDNIGHT` without comments. | **Done (1.2b).** | fixed |
| KN-20 | Doc | `logging_kernel/errors.py` | The hierarchy in the module docstring was stale after `CR-11`. It said `BuilderError` covers "async with no output", which is now a `CompositionError`. It said `ProfileSuggestionWarning` matches outputs, but it matches the whole composition. | **Done (1.2):** both lines describe the current behavior. | fixed |
| KN-21 | Doc | `logging_kernel/errors.py` | `BuilderError`'s docstring said it is raised when ASYNC is queued with no output. | **Done (1.2):** raised when nothing is queued, or when ASYNC has no built handlers to wrap. | fixed |
| KN-22 | Doc | `logging_kernel/errors.py` | `CompositionError`'s example message didn't match the real one ("use a profile" vs "start from a profile"). It said "detail levels" for detail features. | **Done (1.2):** the example is the real message. | fixed |
| KN-23 | Grammar | `logging_kernel/errors.py` | "a composition … is one a profile already says" and "Raised by `normalize_level_name`, so by `with_level()`". | **Done (1.2):** reworded. | fixed |
| KN-24 | Consistency | `logging_kernel/errors.py` | Docstrings didn't follow Standards §1.3. The summary sat on the `"""` line, Sphinx roles were mixed with plain backticks, `HandlerConfigurationError` had no example, and `SharedFileSettingsWarning`'s example showed no call. | **Done (1.2):** all classes follow §1.3. | fixed |
| KN-25 | Consistency | `logging_kernel/errors.py` | `typing.Iterable` is a deprecated alias. (`handlers.py` and `core/specs.py` import from `typing` too; checked in their passes.) | **Done (1.2):** `collections.abc.Iterable`. | fixed |
| KN-26 | Consistency | `logging_kernel/errors.py` | Some messages ended with a period and others didn't. | **Done (1.2):** no final period, like the stdlib. Stated in the module docstring. README example updated. | fixed |
| KN-27 | Dead / Design | `logging_kernel/errors.py` | `BuilderError(name, reason=None)`: no caller used the default message. Both passed `reason=`, and `plan()` passed a fake name, `"<plan>"`. | **Done (1.2):** `BuilderError(message)`. Call sites updated in `core/builder.py` and `catalysts/asynchronous.py` (the second also lost an em dash). | fixed |
| KN-28 | Grammar | `logging_kernel/errors.py` | PyCharm: a 41-word sentence in `LogFileClashError` (line 212). The owner also asked for short sentences and no em dashes everywhere (2026-10-23). | **Done (1.2):** split; em dashes removed from the file's docstrings and messages. The rule joined the shared baseline (Standards §1.4) and was added to LabFrame's and Project A's standards. | fixed |
| KN-29 | Correctness | `logging_kernel/errors.py` | PyCharm: unresolved reference `message` (line 165). `CompositionError` documented a `message` argument it didn't declare. | **Done (1.2):** `CompositionError` and `BuilderError` declare `__init__(self, message)`. | fixed |
| CR-11 | Design | `core/`, `experiments/`, `profiles/` | Experiments mixed four different things: where records go (console, file), extra behavior (rotation), how they look (Rich, JSON) and how they flow (async). So `ROTATING` was a second file experiment, `TIMED_FILE` a third, and `VERBOSE` a second console. File args were one shared bag that every factory had to ignore. | Four kinds with their own methods, specs and options; profiles as recipes; explicit composition rules; INFO default; `TIMED` promoted with `every=`/`at=`/`utc` and size + time naming (owner, 2026-10-22: Continuation D-21 … D-26). **Done:** 281 tests, pyrefly clean, README examples run with warnings as errors. Found while testing: an untargeted profile format spread to a file added on top, so recipes now pin with `on=` (`test_a_profile_keeps_its_features_on_its_own_outputs`). | fixed |
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
| EX-7 | Correctness | `outputs/relay.py` (was `experiments/relay.py`) | A subscriber that logs to a logger which relays back to it re-enters itself without end: one `info()` produced 50 records before a probe's cap (2026-10-22). Documented in `Feedback_Guide.md` §3. | Owner, 2026-10-23: fix it. **Done:** `RelayHandler` skips echoes, records logged inside a subscriber. A thread-local covers the sync path; `AsyncHandler` remembers queued echoes in a `WeakSet` (not a record attribute, which would show in the JSON). Echoes still reach files and consoles. Two tests, sync and `ASYNC`, each shown to fail without the guard. | fixed |
| KN-19 | Design | `logging_kernel/dispatch.py` | One worker thread means one slow output delays every async logger: a 200 ms subscriber held back a record on an unrelated logger by about 212 ms (2026-10-22). This is the trade-off for strict ordering and one thread. Documented in `Feedback_Guide.md` §3. | Owner, 2026-10-23: by design, a feature. Strict order and one thread are the point; keep subscribers fast (`Feedback_Guide.md` §3). | by design |
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

- **Member names that differ from values** (`AGENT`/`"AI_AGENT"`,
  `CONSPIRATOR`/`"CONSPIRACY_THEORIST"`). Selection is by member or by value
  string; the member *name* as a string is not accepted.
- **Asking for a building block again configures it**: options merge per key,
  later values win (Continuation D-25). It is not a duplicate.
- **The registry's tables are checked by tests, not at import** (`CR-18`). Only
  `register_theory` checks at runtime, because only theories are added then.
- **`LabFileHandler` replaces `TimedRotatingFileHandler`**: the stdlib one
  deletes a same-named backup and has no monthly period (Framework Comparison,
  design boundary).
- **A profile can't be subtracted from** (`CR-15`). Profiles are preconfigured
  compositions; to change one, compose by hand.
- **One dispatch worker for every async logger** (`KN-19`). A slow subscriber
  delays the others; that is the price of strict order, and it is a feature.
- **JSON timestamps have no timezone** (`KN-37`). One is added only if a real
  gap shows up.

---

## Updating this doc

1. After each file: fill in its row (scores, tests, notes) and add its
   findings to the ledger with their decision.
2. After each pass: close the pass row, refresh its LOC, and note the commit.
3. After each Step from `Continuation.md`: mark its findings `fixed`, with how
   they were verified.
4. Carry anything left open into the ledger with an ID. Nothing open lives
   only in chat.
