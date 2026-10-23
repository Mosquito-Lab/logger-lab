# logger-lab: Framework Comparison and Capability Map

## Purpose and scope

logger-lab is a **configuration and composition layer over stdlib `logging`**,
not a replacement for it. It packages the logging setup that gets rewritten in
every project (console style, file output, rotation, JSON) into named,
composable pieces, and it always hands back a plain `logging.Logger`.

This assessment is based on the **0.2.0** source tree (2026-10-23) and the
companion docs in this folder. "Missing" means *not provided by logger-lab
itself*; most of it can still be built with stdlib `logging`.

## What logger-lab provides today

| Area | Current provision | Status |
| --- | --- | --- |
| One composer | `lab()…build(name)`: one line for the simple case (`lab().with_profile("investigator").build(__name__)`), the same API for everything else | Available |
| Composition | `lab()` fluent builder over four kinds (outputs, features, formats, catalysts), each with its own method and options. Profiles as recipes, and `on=` targeting. `plan()` previews a composition without building it | Available (redesigned in 0.2.0) |
| Composition rules | Features never bring outputs; one detail feature and one format per output, only where they work; unknown options rejected. `CompositionError` says how to fix it; hand-composing a profile warns `ProfileSuggestionWarning` | Available (0.2.0) |
| Console output | One console: `RICH` (default), `TEXT` or `JSON`, on stderr or stdout; `MINIMAL` / `VERBOSE` detail | Available |
| File output | `TEXT` or `JSON` lines; `ROTATING` by size, `TIMED` on a schedule in the style of `schedule` (`every=`, `unit=` minute to month, `day=`, `at=`, `utc=`), or both, with backups never overwritten and `backup_count` retention | Available (0.2.0) |
| Async logging | `ASYNC` catalyst: the caller only queues; one worker thread per process writes, in order, with tracebacks kept; `drain()`; drained at exit | Available (0.2.0) |
| Live subscribers | `with_subscriber(callback, level=None)` → the `relay` output; works for Qt signals, sockets, tests | Available (0.2.0) |
| GUI apps | `gui` profile: rotating file + relay + `ASYNC`, no console; checked with real PySide6 across threads | Available (0.2.0) |
| Many modules, one file | Each module composes its own logger at its own level; loggers on one path share **one** handler, so rotation works on Windows | Available (0.2.0) |
| Thread safety | Every output, feature and profile is safe from any number of threads. Handler swaps are atomic, and released files never reopen | Available (0.2.0), tested under load |
| Structured output | `JSONFormatter` (Mosquito Lab Standard v1.2: logger name, exceptions with tracebacks, stack, the text format's timestamp) + `log_event()`, which reports the caller as its source | Available |
| Presets | Five profiles (low-noise, dev, archival, AI pipelines, GUI apps), each a recipe you can build on | Available |
| Names | Every building block, profile and theory works by enum member or value string, case-insensitively | Available (0.2.0) |
| Extensibility | Built-in specs in plain tables that the tests check, every profile planned by the tests, and checked theories of any kind; a theory lifecycle from idea to promotion | Available (0.2.0); every theory is still a placeholder |
| Errors | A typed `LabError` hierarchy plus two `UserWarning`s; every composition error names its fix | Available |
| Tests, typing | 190 focused tests (including concurrency, rollover and every fix's regression), pyrefly-clean, `py.typed`; Python 3.10, 3.13, 3.14 | Available |

## How it compares

| Library | What it does especially well | Where logger-lab is stronger or more opinionated | What logger-lab does not provide |
| --- | --- | --- | --- |
| **stdlib `logging`** | The full handler, filter and formatter model; `dictConfig`/`fileConfig`; `QueueHandler`/`QueueListener`; timed and size rotation; the universal ecosystem standard. [logging](https://docs.python.org/3/library/logging.html) · [logging.config](https://docs.python.org/3/library/logging.config.html) · [handlers](https://docs.python.org/3/library/logging.handlers.html) | Named presets and a fluent builder in place of repeated boilerplate or a config dict. Guard rails stdlib doesn't have: in stdlib, two `FileHandler`s on one file is an easy mistake, and with rotation it breaks on Windows. logger-lab opens each file once per process, rejects clashing compositions with an explanation, and its handler swaps are atomic. | No declarative config (dict/YAML/env). It covers a curated subset rather than the full model. (Its async layer deliberately isn't `QueueHandler`/`QueueListener`, which strip tracebacks and need a thread per listener.) |
| **Loguru** | Zero-setup `logger`, `add()` sinks with rotation/retention/**compression**, `@logger.catch`, `bind()`/`contextualize()` for context, thread-safe sinks by default, and `enqueue=True` for process safety and non-blocking calls. Lazy evaluation, colored tracebacks with variable values. [Loguru docs](https://loguru.readthedocs.io/en/stable/) | It stays stdlib-native: it returns real `logging.Logger`s, so third-party libraries and existing handlers work unchanged (Loguru needs an intercept handler for that). Named profiles. Each module composes its own outputs and level explicitly, rather than filtering one global logger. | No compression, no context binding, no exception-catch decorator, no process-safe mode. **Thread safety, non-blocking calls (`ASYNC` ≈ `enqueue=True` within one process) and time-based rotation with retention (`TIMED`, size and time together) are now level with Loguru's.** |
| **structlog** | Processor pipelines, context binding (`bind`, `contextvars`), key/value-first structured events, dev console versus JSON renderers, high performance. [structlog docs](https://www.structlog.org/en/stable/) | Simpler mental model (pick a profile, compose per module). Its JSON schema is fixed and documented, so it is predictable for LLM and pipeline consumers. | No processor chain; no bound or contextvar context (`log_event` takes context per call); no pluggable renderers. |
| **Rich `RichHandler`** | Beautiful console output, tracebacks with locals, markup. [Rich logging](https://rich.readthedocs.io/en/stable/logging.html) | Uses Rich *as* the console's default format and combines it with files and JSON in one call. | Only a few Rich options are exposed: `show_path` follows `VERBOSE`, and the rest (`tracebacks_show_locals` and so on) are fixed. |
| **python-json-logger** | A drop-in JSON `Formatter` with configurable fields, renaming and static fields. [python-json-logger](https://github.com/nhairs/python-json-logger) | A whole logger, not just a formatter; `log_event` gives a consistent event/context/tags shape with the caller's source. | The JSON field set is not configurable (no rename, no static fields, no choice of timestamp key), though it now carries the logger name and exceptions. |

## Gap assessment

0.2.0 closed the trust gaps (tests, safe file handling, thread safety and
consistent naming) and added non-blocking logging and GUI integration.
What remains is mostly **features other libraries have and logger-lab doesn't
yet**, led by context and correlation IDs, and process-safe logging.

| Capability | logger-lab now | Why it matters | Priority | Suggested first increment |
| --- | --- | --- | --- | --- |
| ~~Automated tests~~ | **Closed in 0.2.0:** 190 tests, a leak check, a guard against logging inside the repo, and concurrency tests shown to fail without the fix | n/a | Done | n/a |
| ~~Safe file handling~~ | **Closed in 0.2.0:** one handler per file per process, clash and settings rules, close-on-last-release, released handlers never reopen, foreign handlers never closed | n/a | Done | n/a |
| ~~Thread safety~~ | **Closed in 0.2.0:** atomic handler swaps, locked file table, tested with 8 threads across rotations and rebuilds | n/a | Done | n/a |
| ~~Typing marker~~ | **Closed in 0.2.0:** `py.typed`, and pyrefly-clean | n/a | Done | n/a |
| ~~Time-based rotation and retention~~ | **Closed in 0.2.0:** the `TIMED` feature, with `schedule`-style options from minutes to months, anchored to the calendar. It combines with `ROTATING`, never overwrites a backup, and does monthly too (the stdlib can't) | n/a | Done | n/a |
| Context and correlation IDs | Per-call `context` dict only | Grouping records by request or job is standard (structlog, Loguru `bind`) | **Needs** | `TRACE` theory with `contextvars` |
| ~~Non-blocking dispatch~~ | **Closed in 0.2.0:** `ASYNC`. Caller cost ~25 µs → ~13 µs per written file record (measured 2026-10-23), and it never waits on a slow disk | n/a | Done | n/a |
| Process safety | Not covered: several processes writing one file isn't supported (stdlib doesn't support it either) | multiprocessing workers, several app instances | Should | Extend the dispatch queue to a cross-process one with a single writer process |
| Declarative / env configuration | Code only | Ops want `LOG_LEVEL=DEBUG` or a config file without code changes | Should | `lab().from_env()` or `from_dict()` that maps onto the builder |
| Exception helpers | Rich tracebacks only with the `RICH` format | A `catch`-style decorator is a much-loved Loguru feature | Should | `@lab_catch(logger)` decorator via `logger.exception` |
| ~~Strict validation~~ | **Closed (0.2.0):** unknown level names and invalid numbers raise `InvalidLevelError`; there is no silent fallback | n/a | Done | n/a |
| Configurable JSON schema | Fixed v1.2 schema (with `logger`, `exception`, `stack`; no timezone in `timestamp`) | Aggregators want specific keys | Nice to have | Options: static fields, rename map, version field |
| Redaction | None | Secrets in logs; the `SEC`/`DB` theories need it anyway | Nice to have | A reusable redacting `Filter` in `logging_kernel` |
| Compression of rotated files | None | Disk usage on long runs | Nice to have | A `compress=` option on `ROTATING` / `TIMED`, via `LabFileHandler.rotator` (gzip) |
| ~~GUI / Qt integration~~ | **Closed in 0.2.0:** the `gui` profile + `with_subscriber(signal.emit)`, without logger-lab depending on Qt | n/a | Done | LabFrame adopts it (a LabFrame change) |
| Rate limiting for live subscribers | None | A tight error loop could flood a GUI | Nice to have | The `THROTTLE` feature on `relay` |
| Parent-logger mode | Not provided; each module composes its own logger | Apps wanting the stdlib "configure once, children propagate" setup | Nice to have | Opt-in mode (CR-9 option B); it needs no file sharing, since the children have no handlers |

## Recommended implementation order

1. ~~Tests, safe file handling, thread safety, naming~~ (0.2.0).
2. ~~`ASYNC`, live subscribers and the `gui` profile~~ (0.2.0).
3. ~~The four kinds; promote `TIMED_FILE` to `TIMED`~~ (0.2.0).
4. ~~Cleanliness passes 1–8~~ (round 1, 2026-10-23). Publish 0.2.0, then
   LabFrame adopts the `gui` profile.
5. The feedback layer: `TRACE` (context and correlation IDs) with `LIFECYCLE`
   (standard feedback events), then `THROTTLE` (rate limits for subscribers),
   `PERFORMANCE`, and process safety (`PROCESS`) on the dispatch queue.
6. Then the specialized theories: `HTTP`, `SEC`, `DB`.
7. Configuration from env or a dict, and an exception helper.

## Design boundary to preserve

logger-lab should keep owning **composition and presets**: named behaviors,
sensible defaults, a readable way to combine them, and guard rails that keep
compositions from clashing. It should keep returning plain stdlib loggers and
building on stdlib handlers. It should not grow its own logger class or sink
model (that is Loguru's design) or a processor pipeline (structlog's). When
stdlib already has the primitive (queues, rotation, filters, `dictConfig`),
logger-lab should wrap it as a building block rather than reinvent it. It
replaces one only where it is wrong for logger-lab's guarantees. Timed rotation
is the example. `TimedRotatingFileHandler` deletes a backup with the same name
and has no monthly period. So `LabFileHandler` keeps `BaseRotatingHandler` and
brings its own schedule (`logging_kernel/rollover.py`).
