# Standards and tracker

**Documentation snapshot: 2026-10-22**

This document defines how logger-lab is changed. Every module, function and doc
is held to it.

| Doc | Owns |
|---|---|
| `Standards_and_Tracker.md` (this file) | The rules, plus the high-level workstream tracker |
| `Cleanliness_Tracker.md` | The file-by-file review ledger: scores, finding IDs, decisions, fixes |
| `Continuation.md` | Status, roadmap, the theory pipeline and open design decisions |
| `API_Reference.md` | The public API and the composition logic |
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
  reason (a name collision, a safety invariant, wiring that is implementation
  only), and say why in a short comment.
- Anything public from a package is listed in its `__all__`. Anything imported
  into an `__init__` is either exported there or not imported at all.
- Use section banners (`# Lookup helpers #` boxes) to split longer modules.
- **Comments use plain `#`**, never `#:` doc-comments. A constant's comment
  goes on the same line as the constant:
  `DEFAULT_FILENAME = "app.log"  # Log file name inside the log directory`.
  There is no `Final` on module constants; the module docstring says what they
  are for.

### 1.5 logger-lab additions to the baseline

- **Every experiment, theory and profile accepts `**kwargs`** (see §3.1). This
  is the one signature rule that every extension point shares.
- **Windows is a first-class target.** File-handling behaviour (locks,
  rotation) is verified on Windows, not assumed from POSIX.

---

## 2. Core development standard (logger-lab)

1. **Stdlib-native.** Every entry point returns a plain `logging.Logger`, and
   every handler is a stdlib `logging.Handler` (or a subclass of one). There is
   no custom logger class and no custom sink model. Code that works with
   `logging` keeps working with logger-lab.
2. **Composition is the point, and `lab()` is the one composer.** There is no
   one-call shortcut beside it. An experiment is one atomic behaviour (one
   handler, one format, one destination). A profile only combines experiments.
   The builder composes profiles, experiments and theories into one logger.
   Experiments are designed to be built together.
3. **Experiments never clash.** What gets built together must work together.
   Every experiment and theory owns one **channel** (`CONSOLE`, `FILE`,
   `JSON`, `LIVE`, `DISPATCH`), and a logger holds **at most one experiment per
   channel**. So `standard` and `minimalist` never both print, two handlers
   never write to one file, and a logger never has two dispatchers.
   `DISPATCH` isn't an output: its one experiment (`async`) wraps the others.
   - Two *different* experiments on one channel → `ExperimentClashError`.
     The message names both, where each came from, and the rule.
   - The *same* experiment twice → `DuplicateExperimentWarning`. The first
     instance is kept and the rest are skipped.
   - A profile that clashes with itself fails at registration (import time).
     `rotating_file` is `file` plus rotation, so a profile uses one or the
     other, never both.
4. **Thread-safe by default.** Every experiment and profile is safe to use
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
5. **One file, one handler.** Inside a logger, the one-per-channel rule
   applies (§2.3). *Across* loggers, every log file has exactly one handler
   in the process, shared through `share_file_handler()`. That's what lets
   each module pick its own experiments and level and still write to one
   `app.log`.
   - Same file, same experiment and settings → shared.
   - Same file, same experiment, different settings → shared with the
     **first** settings, plus a `SharedFileSettingsWarning`.
   - Same file, different experiment → `LogFileClashError`. One handler can't
     be both.
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
   | Resolving names (enum or string) to members | `logging_kernel.normalizers` |
   | Registering factories, their channels and profile compositions | `core.registry` (`register_*`) |
   | The one-experiment-per-channel rule | `core.registry.find_channel_clash()` |
   | A profile's composition | its module's `*_EXPERIMENTS` tuple, read by both the profile function and the registry |
   | Assembling a profile's logger for a direct call | `profiles.base.build_profile()` |
   | The default level when none is set | `core.builder.default_level()` |
   | Ordering, de-duplicating and clash-checking a composition | `core.builder.LabBuilder.plan()` |
   | Building the final logger | `core.builder.LabBuilder.build()` |
   | The async queue, its one worker thread, and `drain()` | `logging_kernel.dispatch` |
   | Which factories are dispatchers | `logging_kernel.dispatch.dispatcher` (checked against `DISPATCH` at registration) |
   | Handing records to subscribers | `experiments.relay.RelayHandler` |
   | Default values (paths, sizes, encoding) | `logging_kernel.constants` |
   | The JSON record schema | `logging_kernel.formatters.JSONFormatter` |

7. **Layering: imports point down only.**

   ```text
   constants ← errors ← formatters / handlers        (logging_kernel, base)
            ← core.enums
            ← logging_kernel.normalizers             (needs enums, lazily if needed)
            ← experiments / theories
            ← profiles
            ← core.registry
            ← core.builder
            ← logger_lab/__init__.py
   ```

   Nothing in a lower layer imports a higher one at module level.
8. **Names: enum member or value string, everywhere.** Each experiment,
   profile and theory can be selected by its enum member
   (`ExperimentType.ROTATING_FILE`) or by its value string (`"ROTATING"`),
   case-insensitively. That holds in every builder method:
   `with_experiment()`, `with_profile()` and `with_theory()`. A member's
   *name* may differ from its *value* (`ROTATING_FILE` / `"ROTATING"`,
   `AGENT` / `"AI_AGENT"`, `CONSPIRATOR` / `"CONSPIRACY_THEORIST"`). Docs and
   examples always show the **value** string.
9. **Validate once, at the boundary.** Names are normalized in the `with_*`
   methods. Factories and profile compositions are validated when they are
   registered. Directories are checked in `get_log_dir()`. Clashes are checked
   in `plan()`, before `build()` touches the logger. Factories themselves
   trust their arguments.
10. **The builder is pure until `build()`.** The `with_*` methods only record
   state and return `self`. All I/O (opening files, creating directories)
   happens in `build()`.
11. **Setup code favours clarity; the emit path favours speed.** Building a
   logger happens once, so clarity wins there. Formatting and emitting happen
   on every record, so avoid repeated work there (see `JSONFormatter`'s
   one-time `STANDARD_ATTRS`).
12. **Docs match behaviour**, and that includes the README.
13. **One default level.** No level set → `INFO`, or `WARNING` when `minimalist`
   is part of the logger (`core.builder.default_level`). Invalid levels raise
   `InvalidLevelError`; nothing falls back silently.

---

## 3. Public API standard

### 3.1 Extension-point contracts

| Kind | Signature | Must | Must not |
|---|---|---|---|
| **Experiment** | `name_experiment(level: int = INFO, **kwargs: object) -> list[Handler]` | Accept and ignore unknown kwargs (including `logger_name`, which the builder always passes). Build handlers through `configure_handler()` and directories through `get_log_dir()`. **A file experiment gets its handler from `share_file_handler()`** (a `StayClosedMixin` handler, `NOTSET` level), passing its `kind` and the settings that must agree. State in its docstring which file args it uses. Be registered with its `Channel`. Be thread-safe (§2.4). | Touch a logger, create directories itself, open a file itself, or print. Produce handlers for more than one channel. |
| **Theory** | Same as an experiment | Live in `theories/`. Have a `TheoryType` value. Follow the lifecycle in §3.4. Be registered with `register_theory(..., channel)` once it works. | Be registered before it works (see §3.4). |
| **Profile** | `name(name: str, level: int = INFO, **kwargs: object) -> Logger` | Declare its experiments once as `NAME_EXPERIMENTS = (factory, ...)`, be `build_profile(name, level, *NAME_EXPERIMENTS, **kwargs)`, and be registered with that same tuple. | Combine experiments that clash (§2.3). Its registration fails if it does. |
| **Dispatcher** | `@dispatcher name_experiment(level, *, handlers, logger_name=None, **kwargs) -> list[Handler]` | Wrap *handlers* (the logger's built outputs) and return the handlers that replace them; release them when released. Be registered on `Channel.DISPATCH`. Raise `BuilderError` if there's nothing to wrap. | Write records on the calling thread's behalf without the order and exit guarantees of `logging_kernel.dispatch`. |
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
  (`logger_lab.core`, `logger_lab.logging_kernel`, `logger_lab.experiments`,
  `logger_lab.profiles`).
- A removal or rename of anything public is listed in `Continuation.md` with
  the version it changed in.

### 3.4 Theory lifecycle

| Stage | What exists | Registered? |
|---|---|---|
| **Idea** | A `theories/name_exp.py` file whose module docstring states the mechanism and the purpose | No |
| **Placeholder** | Plus a `TheoryType` value | No. Selecting it raises `TheoryNotFoundError` |
| **Trial** | A working factory that follows §3.1, registered with `register_theory(theory, factory, channel)`, runnable with `python -m logger_lab.theories._test_theory NAME` | Yes, as a theory |
| **Promoted** | Moved to `experiments/` with an `ExperimentType` value, and its `TheoryType` value removed | Yes, as an experiment |

**Promotion checklist:** follows §3.1 · has tests (§4) · **is thread-safe,
with a concurrency test (§2.4)** · docstrings follow §1.3 · has an API
Reference row · has a README row · shows it can't clash (§2.3, §2.5) · has a
passing pass row in the cleanliness tracker.

The lifecycle is implemented (Step 5, 2026-10-22). Theories are selected with
`with_theory(theory, **options)`, by member or value string. *options* reach only that theory's factory.

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
- **What must be pinned:** every enum member, selected by member and by value
  string, through every entry point · every experiment's handler type and file
  args · every profile's experiments · clash detection · file sharing and
  release · thread safety under load (many threads, rotation, rebuilds) · the
  JSON schema · every error path.
- **No leaks:** after every test, the shared file table must be empty. Every
  file a test opened was released.
- **A concurrency test must be able to fail.** Check it once against the bug
  it guards (for example, with sharing patched out, the rotation test loses
  records and hits `WinError 32`).
- **Recorded baseline (2026-10-22, Windows, Python 3.10):** `pytest` **181
  passed** (the concurrency tests passed 5 runs in a row). `pyrefly`
  **0 errors, 0 warnings, 3 suppressed**: two deliberate wrong-type calls in
  tests, and one `inspect.currentframe()` that pyrefly treats as possibly
  `None`.
- **Integration check for the `gui` profile:** run against LabFrame's own
  environment (real PySide6), a record logged on a worker thread reaches a Qt
  slot on the GUI thread (`Continuation.md`, 0.2.0 changes).

---

## 5. High-level tracker

| Workstream | Status | Current note |
|---|---|---|
| Experiments (8) | Done | Each registered with its channel; `relay` and `async` added after `3adfa9c`. Cleanliness review pending (pass 3) |
| Profiles (5) | Done | Declared `*_EXPERIMENTS` tuples. `gui` added after `3adfa9c` for LabFrame |
| Builder (`lab()`, the only composer) | Done | `with_file_args()`, `with_theory()`, `with_subscriber()`, `plan()`; `get_logger()` removed (D-19) |
| Async dispatch | Done (0.2.0) | One worker thread per process, tracebacks kept, `drain()`, drained at exit |
| Composition rules (one per channel, duplicates warn) | Done 2026-10-22 | Per logger (§2.3) |
| One file, one handler, across loggers (`CR-9`) | Done 2026-10-22 | `share_file_handler()`; per-module levels and experiments (§2.5) |
| Thread safety (D-9) | Done 2026-10-22 | Atomic handler swaps (`CR-10`), stay-closed file handlers, concurrency tests (`TS-4`) |
| Handler closing | Done 2026-10-22 | Released when last, closed only if logger-lab created it |
| Name resolution (enum + value) | Done | Experiments, profiles and theories; pinned by tests |
| Theory system | Done 2026-10-22 | Lifecycle §3.4 |
| `TIMED_FILE` theory | **Trial** | Registered and tested; promotion pending (`Continuation.md` §3) |
| Theories `TRACE` … `DB` | Placeholder | Ranked in `Continuation.md` §3 |
| Test and type-check baseline | Done | 181 passed · pyrefly clean |
| LabFrame adoption of the `gui` profile | Not started | A LabFrame-side change, once 0.2.0 is published |
| Standards (this doc) | Done 2026-10-22 | Baseline §1 to be mirrored into LabFrame and Project A |
| Cleanliness passes | Paused | Every flagged finding was fixed on 2026-10-22; the passes still score and re-check each file |
| README | Done 2026-10-22 | |

---

## 6. Immediate priority

Async, relay, the `gui` profile and the `TIMED_FILE` trial (all still 0.2.0)
are built and verified, including against LabFrame's real PySide6. Next: the owner
reviews the preview and commits. Then come LabFrame's adoption of the `gui`
profile, `TIMED_FILE` promotion, and the cleanliness passes (paused by the
owner, 2026-10-22).
