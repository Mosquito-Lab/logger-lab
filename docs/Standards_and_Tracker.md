# Standards and tracker

**Documentation snapshot: 2026-10-23**

This document defines how logger-lab is changed. Every module, function and doc
is held to it.

| Doc | Owns |
|---|---|
| `Standards_and_Tracker.md` (this file) | The rules, plus the high-level workstream tracker |
| `Cleanliness_Tracker.md` | The file-by-file review ledger: scores, finding IDs, decisions, fixes |
| `Continuation.md` | Status, roadmap, the theory pipeline and open design decisions |
| `API_Reference.md` | The public API and the composition logic |
| `Feedback_Guide.md` | How records reach people, files, machines and live UIs: async, subscribers, Qt and other event loops, with guarantees and limits |
| `Framework_Comparison.md` | Where logger-lab stands against other logging libraries |

Status and task order live **only** in `Continuation.md`. Findings live **only**
in `Cleanliness_Tracker.md`. Neither is repeated here.

---

## 1. Baseline standard (shared by every project)

> **Baseline.** Section 1 is copied word for word into every project's standards
> doc (logger-lab, LabFrame, Project A, …). A project may **add** rules under
> §1.5 for its own special cases, but it never removes or rewords a baseline
> rule. To change the baseline, change it in every project in the same pass.

### 1.1 Collaboration

1. **Break work into steps and take one problem at a time.** List what needs
   doing, let the owner choose the order, and do not run everything at once.
2. **Show the proposed change before writing it**, unless the owner has
   explicitly approved that change. An approval covers that change only, not
   the next one.
3. **Findings are listed, not silently fixed.** A problem found while doing
   something else is recorded with an ID, and the owner decides what happens
   to it.
4. **Check the real source.** Describe what the code does now, read from the
   file itself and its callers. Do not rely on a previous doc's description of
   it, or on what a name implies.
5. **Use git only when the owner asks.** Preserve the owner's unrelated local
   changes.
6. **Docs:** the trackers (the cleanliness ledger and the continuation/status
   doc) are updated in the same turn as the approved work they record. Every
   other doc changes only when the owner asks.
7. **Report honestly.** After each step, say what was verified and how, what
   was not verified, and what remains. "Not run" stays "not run".

### 1.2 Code

1. **Prefer simple code.** Use plain functions, lists, dicts and loops unless
   an abstraction solves a real problem that exists now.
2. **One owner per concern.** Every responsibility lives in exactly one place
   (each project lists its owners in §2).
3. **Validate once, at the boundary.** Check inputs where they enter. Code
   further in trusts what it was given.
4. **Fail loudly and with types.** Predictable failures raise the project's own
   exception types, with a message that says what to do. Never `print()` an
   error. Never let a predictable failure surface as a bare `KeyError` or
   `TypeError`.
5. **Use keyword arguments** when a call has more than one meaningful argument.
6. **Names describe intent.** They should be clear first, and a little fun
   where it fits naturally (`get_stylish()`, `conspiracy_theorist`).
   Clear-and-plain beats clever-but-vague.
7. **Optimize measured costs.** A shorter loop is not automatically an
   improvement. Optimize the paths that actually run often or cost I/O.
8. **No side effects on import**, beyond deliberate registration.
9. **Imports point down a declared layering** (each project defines it in §2).

### 1.3 Docstrings

Every function and class gets a docstring. That includes internal helpers, and
any `__init__` that does real work. In order, wherever they apply, it answers:

1. **What does the library do here automatically?**
2. **What must the caller supply?** For an extension point, give the exact
   signature to implement.
3. **How is it used?** A short `Example::`.

```python
def function(arg: Type) -> ReturnType:
    """
    One-line summary.

    One or two sentences: why it exists and which side of the
    library/consumer line it sits on.

    Note: anything surprising or easy to misuse.

    Args:
        arg: ...
    Returns:
        ...
    Raises:
        `SomeError`: when ...
    Example::
        function(value)
    """
```

- The docstring matches the code: Args, Returns and Raises are complete and
  use current names.
- Keep it short. If something needs a paragraph to explain, the code can
  usually be clearer.
- An extension point's docstring **is** its implementation guide. Someone
  should be able to write a correct implementation from the docstring alone.

### 1.4 House style

- Every file starts with a module docstring and ends with one blank line.
- Type hints use `X | None`, not `Optional[X]` or `Union[...]`.
- Use American spelling (`normalize`, `color`, `serialize`).
- **Don't use a `_` prefix by default.** Only mark something private for a real
  reason, and say why in a short comment. Real reasons are a name collision, a
  safety invariant, or wiring that is implementation only.
- Anything public from a package is listed in its `__all__`. Anything imported
  into an `__init__` is either exported there or not imported at all.
- Use section banners (`# Lookup helpers #` boxes) to split longer modules.
- **Comments use plain `#`**, never `#:` doc-comments. A constant's comment
  goes on the same line as the constant:
  `DEFAULT_FILENAME = "app.log"  # Log file name inside the log directory`.
  There is no `Final` on module constants; the module docstring says what they
  are for.
- **Write short, plain sentences.** Join thoughts with a period, not an em
  dash (—) or a double hyphen (`--`). Split a sentence once it runs past about
  25 words. PyCharm flags long ones. This holds for docstrings, comments,
  error messages, docs and chat.

### 1.5 logger-lab additions to the baseline

- **Every building block declares its options** (see §3.1). An option it
  doesn't declare is rejected, never ignored; this is the one rule every
  extension point shares.
- **Windows is a first-class target.** File-handling behavior (locks,
  rotation) is verified on Windows, not assumed from POSIX.

---

## 2. Core development standard (logger-lab)

1. **Stdlib-native.** Every entry point returns a plain `logging.Logger`, and
   every handler is a stdlib `logging.Handler` (or a subclass of one). There is
   no custom logger class and no custom sink model. Code that works with
   `logging` keeps working with logger-lab.
2. **Composition is the point, and `lab()` is the one composer.** There is no
   one-call shortcut beside it. A logger is composed from **four kinds** of
   building block, each with its own method:
   - an **output**: where feedback goes (`with_output`);
   - a **feature**: extra behavior on an output (`with_feature`);
   - a **format**: how a record looks (`with_format`);
   - a **catalyst**: how every record flows (`with_catalyst`).

   A **profile** is a common composition written as builder calls. A **theory**
   is a building block of any kind still being researched. Options live on the
   building blocks, and asking for one again configures it.
3. **Compositions are explicit and never clash.** What gets built together
   must work together, and nothing is added behind the user's back.
   - **A feature or format never brings an output.** It attaches to every
     queued output it fits, or to `on=`'s output; if none fits, that's a
     `CompositionError` naming the fix (add the output, or use a profile).
   - **One output of each kind per logger; one detail feature and one format
     per output, only where they work** (`ROTATING` is file-only, `RICH`
     console-only, `MINIMAL` / `VERBOSE` don't apply to `JSON`).
   - **Options are declared.** An undeclared option or a bad value is a
     `CompositionError`, listing the valid ones.
   - **One profile per builder, one catalyst per group** (`dispatch`).
   - **Profiles are the way to simplify.** Composing by hand what a profile
     already provides warns `ProfileSuggestionWarning`. The suggestion is tested
     first: the composition is replayed on the profile and must come out the
     same, so following it never adds anything and never clashes. Anything that
     would actually break is an error, not a warning.
   - A profile's recipe pins its features and formats with `on=` wherever a
     later output could also take them. The tests plan every profile, so a
     profile that breaks a rule fails there.
4. **Thread-safe by default.** Every building block and profile is safe to use
   from any number of threads in one process. That means:
   - **Handlers are locked.** Every write goes through the handler's own lock,
     which stdlib handlers already provide.
   - **Formatters hold no state.** Nothing is shared between records.
   - **No file is opened by more than one handler.** Loggers writing to the
     same path share one handler (§2.5).
   - **Swapping handlers onto a logger is atomic.** A thread that is logging
     sees the old handlers or the new ones, never a mix.

   A theory may relax this during trial, but it must be thread-safe, with
   tests, to be promoted (§3.4). Process safety (several processes writing to
   one file) is a separate, opt-in feature; it is not implied.
5. **One file, one handler.** Inside a logger, the composition rules apply
   (§2.3). *Across* loggers, every log file has exactly one handler in the
   process, shared through `share_file_handler()`. That's what lets each
   module pick its own composition and level and still write to one
   `app.log`. A file's **kind** is its format plus its rotation features
   (`FILE[TEXT]+ROTATING`).
   - Same file, same kind and settings → shared.
   - Same file, same kind, different settings → shared with the **first**
     settings, plus a `SharedFileSettingsWarning`.
   - Same file, different kind → `LogFileClashError`. One handler can't be
     both.
   - A backup is never overwritten: rotation names a taken backup with a
     counter instead.
   - A shared handler has no level of its own (`NOTSET`); each logger's level
     filters its own records. It closes when its last logger releases it.
   - logger-lab only ever closes handlers it created. Anything else on a
     logger is detached, never closed.
6. **One owner per concern:**

   | Concern | Owner |
   |---|---|
   | Creating log directories | `logging_kernel.handlers.get_log_dir()` |
   | Setting a handler's level and formatter, and marking it as logger-lab's | `logging_kernel.handlers.configure_handler()` |
   | One handler per log file, across loggers | `logging_kernel.handlers.share_file_handler()` and `SHARED_FILES` |
   | Putting handlers on a logger (atomic swap) | `logging_kernel.handlers.install_handlers()` |
   | Letting go of a handler (close only when last and ours) | `logging_kernel.handlers.release_handler()` |
   | Detaching every handler from a logger | `logging_kernel.handlers.clear_handlers()` |
   | Resolving names (enum or string) to members | `logging_kernel.normalizers.normalize_name()` |
   | What each building block fits, its options and defaults | its spec (`core.specs`), next to the block |
   | The built-in tables, and registering a theory | `core.registry` (`OUTPUTS` … `PROFILES`, `register_theory()`) |
   | A profile's composition | its module's recipe (`ProfileSpec`) |
   | Checking every spec is well formed and every profile composes | `tests/test_registry.py` |
   | Every composition rule | `core.builder.LabBuilder.plan()` (and each spec's `check`) |
   | Building the final logger | `core.builder.LabBuilder.build()` |
   | The default level when none is set | `core.builder.LabBuilder.build()` (always `INFO`) |
   | Console handlers | `outputs.console.build_console()` |
   | The file handler, its kind and settings | `outputs.file.build_file()` and `logging_kernel.handlers.LabFileHandler` |
   | Rollover periods, boundaries and backup labels | `logging_kernel.rollover` (`SizeRule`, `TimeRule`) |
   | The text layouts | `logging_kernel.formatters.TEXT_LAYOUTS` |
   | The async queue, its one worker thread, and `drain()` | `logging_kernel.dispatch` |
   | Handing records to subscribers | `outputs.relay.RelayHandler` |
   | Default values (paths, sizes, encoding) | `logging_kernel.constants` |
   | The JSON record schema | `logging_kernel.formatters.JSONFormatter` |

7. **Layering: imports point down only.**

   ```text
   constants ← errors ← rollover / formatters / handlers / dispatch   (logging_kernel, base)
            ← core.enums ← core.specs
            ← logging_kernel.normalizers             (needs enums, lazily if needed)
            ← outputs / features / formats / catalysts / theories
            ← profiles                               (recipes; the builder only as a type)
            ← core.registry                          (plain tables of the specs)
            ← core.builder
            ← logger_lab/__init__.py
   ```

   Nothing in a lower layer imports a higher one at module level.
8. **Names: enum member or value string, everywhere.** Each building block,
   profile and theory can be selected by its enum member (`Feature.ROTATING`)
   or by its value string (`"ROTATING"`), case-insensitively. That holds in
   every builder method and in `on=`. Each method takes only its own kind;
   another kind's name is an `InvalidNameError`. A member's *name* may differ
   from its *value* (`AGENT` / `"AI_AGENT"`, `CONSPIRATOR` /
   `"CONSPIRACY_THEORIST"`). Docs and examples always show the **value**
   string.
9. **Validate once, at the boundary.** Names are normalized in the `with_*`
   methods. The built-in specs and profiles are checked by the tests, and a
   theory when it is registered. Options and composition rules are checked in
   `plan()`, before `build()` touches the logger. Directories are checked in
   `get_log_dir()`. An output's `build` trusts the plan it gets.
10. **The builder is pure until `build()`.** The `with_*` methods only record
   state and return `self`. All I/O (opening files, creating directories)
   happens in `build()`.
11. **Setup code favors clarity; the emit path favors speed.** Building a
   logger happens once, so clarity wins there. Formatting and emitting happen
   on every record, so avoid repeated work there (see `JSONFormatter`'s
   one-time `STANDARD_ATTRS`).
12. **Docs match behavior**, and that includes the README.
13. **One default level.** No level set → `INFO`, for every logger and every
   profile; quieter or louder is set intentionally with `with_level()`.
   Invalid levels raise `InvalidLevelError`; nothing falls back silently.

---

## 3. Public API standard

### 3.1 Extension-point contracts

| Kind | Signature | Must | Must not |
|---|---|---|---|
| **Output** | `OutputSpec(member, build: (OutputPlan) -> list[Handler], options, formats, default_format, check)` | Declare every option with its default, and the formats it accepts. Build handlers through `configure_handler()` and directories through `get_log_dir()`. **A file output gets its handler from `share_file_handler()`** (a `StayClosedMixin` handler, `NOTSET` level), passing its `kind` and the settings that must agree. Interpret the features and format it is given. Be thread-safe (§2.4). | Touch a logger, create directories itself, open a file itself, or print. |
| **Feature** | `FeatureSpec(member, fits, options, group, formats, check)` | Say which outputs it fits, its exclusive group if any, and the formats it works with. Validate its options in `check`, raising `CompositionError`. | Bring an output with it, or act on an output it doesn't fit. |
| **Format** | `FormatSpec(member, fits, options)` | Say which outputs it fits; the outputs render it. | Fit an output that can't render it. |
| **Catalyst** | `CatalystSpec(member, build: (handlers, *, logger_name, options) -> list[Handler], options, group)` | Wrap *handlers* (the logger's built outputs) and return the handlers that replace them; release them when released. Raise `BuilderError` if there's nothing to wrap. | Write records on the calling thread's behalf without the order and exit guarantees of `logging_kernel.dispatch`. |
| **Theory** | The spec of its kind, with a `TheoryType` member | Live in `theories/`. Follow the lifecycle in §3.4. Be registered with `register_theory(kind, spec)` once it works. | Be registered before it works (see §3.4). |
| **Profile** | `ProfileSpec(member, recipe: (builder) -> builder, summary)` | Only call the builder; pin features and formats with `on=` where a later output could take them. | Break a composition rule (§2.3). The tests plan every profile and fail if it does. |
| **Builder method** | `with_x(self, ...) -> "LabBuilder"` | Normalize and record its input, then return `self`. | Do any I/O. |

### 3.2 Errors

- Every error the library raises is a `LabError` subclass, and each one sits
  in the hierarchy documented in `errors.py` and the API Reference.
- An error message names the bad value and how to fix it (for example, it
  lists the valid names).
- A wrapped low-level error is raised with `from err`.
- A new failure mode gets a new subclass under the right branch: registry,
  configuration or builder.

### 3.3 Public surface

- `logger_lab/__init__.py`'s `__all__` lists exactly what consumers import
  from the top level.
- Subpackage `__init__`s export their own layer's tools
  (`logger_lab.core`, `logger_lab.logging_kernel`, `logger_lab.outputs`,
  `logger_lab.features`, `logger_lab.formats`, `logger_lab.catalysts`,
  `logger_lab.profiles`).
- A removal or rename of anything public is listed in `Continuation.md` with
  the version it changed in.

### 3.4 Theory lifecycle

| Stage | What exists | Registered? |
|---|---|---|
| **Idea** | A `theories/name_exp.py` file whose module docstring states the mechanism, the purpose and the likely kind (or "helper") | No |
| **Placeholder** | Plus a `TheoryType` value | No. Selecting it raises `TheoryNotFoundError` |
| **Trial** | A working spec of its kind that follows §3.1, registered with `register_theory(kind, spec)`, and tried with `with_theory()` in a test | Yes, as a theory |
| **Promoted** | Moved into its kind's package with a member of that kind's enum, and its `TheoryType` value removed | Yes, as that kind |

**Helpers.** Some ideas aren't a building block: `LIFECYCLE` is a function on
top of `log_event`, `PERFORMANCE` a decorator, and `DB` hooks installed on an
engine. Their idea file says "helper". A helper can't be selected with
`with_theory()`, so it skips the Trial stage's registration. It is tried in
tests, and promoted into the public API beside `log_event`, not into a kind's
package. Its `TheoryType` value is removed when it is promoted.

**Promotion checklist:**
- follows §3.1;
- has tests (§4);
- **is thread-safe, with a concurrency test (§2.4)**;
- has docstrings that follow §1.3;
- has an API Reference row and a README row;
- shows it can't clash (§2.3, §2.5);
- has a passing row in the cleanliness tracker.

The lifecycle is implemented (Step 5, 2026-10-22). Theories are selected with
`with_theory(theory, on=None, **options)`, by member or value string, and act
as the kind they were registered as. `TIMED_FILE` was the first promotion: it
became the `TIMED` feature (2026-10-22).

---

## 4. Verification standard

From the repository root:

```bash
uv run pytest -q
```

```bash
uv run pyrefly check
```

- **Setup:** the `uv_build` backend means `uv sync` installs `logger_lab` as
  editable. `pytest` and `pyrefly` are in the `dev` dependency group. Tests
  live in `tests/` and the pyrefly config is in `pyproject.toml`.
- **Tests run offline and never log to a file inside the repository.** Every
  test runs in its own `tmp_path` (outside the repo) and its handlers are
  closed afterwards. `tests/conftest.py` enforces this: a test fails if it
  leaves a file handler pointing inside the repo, and the run fails if any
  `*.log*` file appears there.
- **What must be pinned:**
  - every enum member of every kind, selected by member and by value string,
    through every entry point;
  - every profile's composition;
  - every composition rule and its message;
  - options: defaults, merging, unknown names and bad values;
  - the suggestion warning;
  - the console's stream, formats and detail;
  - file formats (JSON lines);
  - rotation: every `unit=`, with `every=`, `day=`, `at=` and `utc=`,
    calendar anchoring, combined naming that never overwrites, and retention;
  - file sharing and release;
  - thread safety under load (many threads, rotation, rebuilds);
  - the JSON schema;
  - every error path.
- **No leaks:** after every test, the shared file table must be empty. Every
  file a test opened was released.
- **A concurrency test must be able to fail.** Check it once against the bug
  it guards (for example, with sharing patched out, the rotation test loses
  records and hits `WinError 32`).
- **Tests are few and pointed.** One test per behavior, with edge cases as their
  own cases. A list of members or values is looped inside one test, not
  parametrized into dozens. A bug fix lands with a test shown to fail without
  the fix.
- **Recorded baseline (2026-10-23, Windows):** `pytest` **190 passed** on Python
  3.10, 3.13 and 3.14 (the suite was redesigned down from 316). `pyrefly`
  reports **0 diagnostics and 10 suppressed errors**, from six
  `pyrefly: ignore` comments. Three read option values already validated in
  `outputs/file.py`. One marks a deliberate wrong-type call in a test. Two are
  `inspect.currentframe()` calls that pyrefly treats as possibly `None`. Every
  README example runs on its own, with warnings as errors.
- **Integration check for the `gui` profile:** run it in LabFrame's own
  environment, with real PySide6. A record logged on a worker thread must reach
  a Qt slot on the GUI thread (`Continuation.md`, 0.2.0 changes).

---

## 5. High-level tracker

| Workstream | Status | Current note |
|---|---|---|
| The four kinds (D-21) | Done 2026-10-22 | Outputs (3), features (4), formats (3), catalysts (1), each with its own spec, method and options; experiments and channels removed. Cleanliness pass 3 closed 2026-10-23 |
| Profiles (5) | Done 2026-10-22 | Recipes of builder calls, planned by the tests; `build_profile` and the profile functions removed |
| Builder (`lab()`, the only composer) | Done 2026-10-22 | `with_output/feature/format/catalyst()`, `with_theory()`, `with_subscriber()`, `plan()`; `with_file_args()` and `get_logger()` removed |
| Async dispatch | Done (0.2.0) | The `ASYNC` catalyst: one worker thread per process, tracebacks kept, `drain()`, drained at exit |
| Composition rules | Done 2026-10-22 | Explicit: no implicit outputs, `on=`, groups, declared options, `ProfileSuggestionWarning` (§2.3) |
| One file, one handler, across loggers (`CR-9`) | Done 2026-10-22 | `share_file_handler()` keyed by kind (format + rotation); per-module levels and compositions (§2.5) |
| Rotation (`ROTATING`, `TIMED`, both) | Done 2026-10-22 | `LabFileHandler` + `rollover.py`; `schedule`-style options (`every=`, `unit=`, `day=`, `at=`, `utc=`), calendar-anchored; backups never overwritten |
| Thread safety (D-9) | Done 2026-10-22 | Atomic handler swaps (`CR-10`), stay-closed file handlers, concurrency tests (`TS-4`) |
| Handler closing | Done 2026-10-22 | Released when last, closed only if logger-lab created it |
| Name resolution (enum + value) | Done | Every kind, profiles, theories and `on=`; pinned by tests |
| Theory system | Done 2026-10-22 | Lifecycle §3.4 |
| `TIMED_FILE` theory | Promoted 2026-10-22 | Now the `TIMED` feature |
| Theories `TRACE` … `DB` | Placeholder | Ranked in `Continuation.md` §3 |
| Test and type-check baseline | Done | 190 passed (redesigned 2026-10-23) · pyrefly clean |
| LabFrame adoption of the `gui` profile | Not started | A LabFrame-side change, once 0.2.0 is published |
| Standards (this doc) | Done 2026-10-22 | Baseline §1 to be mirrored into LabFrame and Project A |
| Cleanliness passes | Done 2026-10-23 | Round 1: all eight passes closed and every finding fixed (`Cleanliness_Tracker.md`) |
| README | Done 2026-10-23 | Re-checked against the code in pass 8 |

---

## 6. Immediate priority

0.2.0 is built, verified and through round 1 of the cleanliness passes. Next,
the owner commits it, then merges to `main` and publishes when ready. After
that comes LabFrame's adoption of the `gui` profile (its `channel.py` still
uses 0.1's `get_logger`), then the feedback layer (`Continuation.md` §3).
