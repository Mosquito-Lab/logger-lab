# logger-lab: Framework Comparison and Capability Map

## Purpose and scope

logger-lab is a **configuration and composition layer over stdlib `logging`**,
not a replacement for it. It packages the logging setup that gets rewritten in
every project (console style, file output, rotation, JSON) into named,
composable pieces, and it always hands back a plain `logging.Logger`.

This assessment is based on the **0.2.0** source tree (2026-10-22) and the
companion docs in this folder. "Missing" means *not provided by logger-lab
itself*; most of it can still be built with stdlib `logging`.

## What logger-lab provides today

| Area | Current provision | Status |
| --- | --- | --- |
| One-call setup | `get_logger(name, profile=… / experiment=… / theory=…)` | Available |
| Composition | `lab()` fluent builder: profile, experiments and theories, level, file args. `plan()` previews a composition without building it | Available |
| Composition rules | At most one experiment per channel (console, file, JSON). A clash raises `ExperimentClashError`; a duplicate warns and keeps the first | Available (0.2.0) |
| Console output | Rich (`standard`), full-context (`verbose`), terse (`minimalist`) | Available |
| File output | Plain file and size-rotating file, configurable through `with_file_args()` | Available |
| Many modules, one file | Each module composes its own logger at its own level; loggers on one path share **one** handler, so rotation works on Windows | Available (0.2.0) |
| Thread safety | Every experiment and profile is safe from any number of threads. Handler swaps are atomic, and released files never reopen | Available (0.2.0), tested under load |
| Structured output | `JSONFormatter` (Mosquito Lab Standard v1) + `log_event()`, which reports the caller as its source | Available |
| Presets | Four profiles for prod, dev, archival and AI pipelines | Available |
| Names | Every experiment, profile and theory works by enum member or value string, case-insensitively | Available (0.2.0) |
| Extensibility | Validated registration for experiments, profiles (compositions checked when registered) and theories; a theory lifecycle with a test harness | Available (0.2.0); every theory is still a placeholder |
| Errors | A typed `LabError` hierarchy plus two `UserWarning`s | Available |
| Tests, typing | 112 tests (including concurrency), pyrefly-clean, `py.typed` | Available (0.2.0) |

## How it compares

| Library | What it does especially well | Where logger-lab is stronger or more opinionated | What logger-lab does not provide |
| --- | --- | --- | --- |
| **stdlib `logging`** | The full handler, filter and formatter model; `dictConfig`/`fileConfig`; `QueueHandler`/`QueueListener`; timed and size rotation; the universal ecosystem standard. [logging](https://docs.python.org/3/library/logging.html) · [logging.config](https://docs.python.org/3/library/logging.config.html) · [handlers](https://docs.python.org/3/library/logging.handlers.html) | Named presets and a fluent builder in place of repeated boilerplate or a config dict. Guard rails stdlib doesn't have: in stdlib, two `FileHandler`s on one file is an easy mistake, and with rotation it breaks on Windows. logger-lab opens each file once per process, rejects clashing compositions with an explanation, and its handler swaps are atomic. | No declarative config (dict/YAML/env). Queue and timed handlers are not wrapped yet (they are theories). It covers a curated subset rather than the full model. |
| **Loguru** | Zero-setup `logger`, `add()` sinks with rotation/retention/**compression**, `@logger.catch`, `bind()`/`contextualize()` for context, thread-safe sinks by default, and `enqueue=True` for process safety and non-blocking calls. Lazy evaluation, coloured tracebacks with variable values. [Loguru docs](https://loguru.readthedocs.io/en/stable/) | It stays stdlib-native: it returns real `logging.Logger`s, so third-party libraries and existing handlers work unchanged (Loguru needs an intercept handler for that). Named profiles. Each module composes its own outputs and level explicitly, rather than filtering one global logger. | No retention or compression, no context binding, no exception-catch decorator, no non-blocking or process-safe mode, no time-based rotation. **Thread safety is now level with Loguru's.** |
| **structlog** | Processor pipelines, context binding (`bind`, `contextvars`), key/value-first structured events, dev console versus JSON renderers, high performance. [structlog docs](https://www.structlog.org/en/stable/) | Simpler mental model (pick a profile, compose per module). Its JSON schema is fixed and documented, so it is predictable for LLM and pipeline consumers. | No processor chain; no bound or contextvar context (`log_event` takes context per call); no pluggable renderers. |
| **Rich `RichHandler`** | Beautiful console output, tracebacks with locals, markup. [Rich logging](https://rich.readthedocs.io/en/stable/logging.html) | Uses Rich *as* the `standard` experiment and combines it with files and JSON in one call. | Only a few Rich options are exposed (`show_path`, `tracebacks_show_locals` and so on are hard-coded). |
| **python-json-logger** | A drop-in JSON `Formatter` with configurable fields, renaming and static fields. [python-json-logger](https://github.com/nhairs/python-json-logger) | A whole logger, not just a formatter; `log_event` gives a consistent event/context/tags shape with the caller's source. | The JSON field set is not configurable (no rename, no static fields, no choice of timestamp key), and it doesn't include the logger's name (`KN-11`). |

## Gap assessment

0.2.0 closed the trust gaps: tests, safe file handling, thread safety and
consistent naming. What remains is mostly **features other libraries have and
logger-lab doesn't yet**, led by time rotation, context, and non-blocking or
process-safe logging.

| Capability | logger-lab now | Why it matters | Priority | Suggested first increment |
| --- | --- | --- | --- | --- |
| ~~Automated tests~~ | **Closed in 0.2.0:** 112 tests, a leak check, a guard against logging inside the repo, and concurrency tests shown to fail without the fix | — | Done | — |
| ~~Safe file handling~~ | **Closed in 0.2.0:** one handler per file per process, clash and settings rules, close-on-last-release, released handlers never reopen, foreign handlers never closed | — | Done | — |
| ~~Thread safety~~ | **Closed in 0.2.0:** atomic handler swaps, locked file table, tested with 8 threads across rotations and rebuilds | — | Done | — |
| ~~Typing marker~~ | **Closed in 0.2.0:** `py.typed`, and pyrefly-clean | — | Done | — |
| Time-based rotation and retention | Size rotation only | Daily logs and "keep 7 days" are the most common ops request (Loguru's headline feature) | **Needs** | `TIMED_FILE` theory (FILE channel, through `share_file_handler()`), then promote it |
| Context and correlation IDs | Per-call `context` dict only | Grouping records by request or job is standard (structlog, Loguru `bind`) | **Needs** | `TRACE` theory with `contextvars` |
| Non-blocking dispatch | Formatting and file writes run on the calling thread (~24 µs per written record, measured) | Async apps and GUI threads (LabFrame) shouldn't wait on disk | **Needs** | `ASYNC` theory with `QueueHandler`/`QueueListener` + `atexit` stop |
| Process safety | Not covered: several processes writing one file isn't supported (stdlib doesn't support it either) | multiprocessing workers, several app instances | Should | The same `ASYNC` queue, with one listener process doing the writing |
| Declarative / env configuration | Code only | Ops want `LOG_LEVEL=DEBUG` or a config file without code changes | Should | `lab().from_env()` or `from_dict()` that maps onto the builder |
| Exception helpers | Rich tracebacks only on `standard` | A `catch`-style decorator is a much-loved Loguru feature | Should | `@lab_catch(logger)` decorator via `logger.exception` |
| Strict validation | Unknown levels quietly become `INFO` (`KN-2`) | Typos hide misconfiguration | Should | Opt-in strict mode that raises `InvalidLevelError` |
| Configurable JSON schema | Fixed v1 schema, with no logger name (`KN-11`) | Aggregators want specific keys; shared streams need the logger | Nice to have | A `"logger"` field first, then options: static fields, rename map, version field |
| Redaction | None | Secrets in logs; the `SEC`/`DB` theories need it anyway | Nice to have | A reusable redacting `Filter` in `logging_kernel` |
| Compression of rotated files | None | Disk usage on long runs | Nice to have | `rotator`/`namer` hooks on the shared rotating handler (gzip) |
| GUI / Qt integration | None (LabFrame has its own relay) | Windowed apps lose stdout | Nice to have | GUI profile built on `ASYNC` |
| Parent-logger mode | Not provided; each module composes its own logger | Apps wanting the stdlib "configure once, children propagate" setup | Nice to have | Opt-in mode (CR-9 option B); it needs no file sharing, since the children have no handlers |

## Recommended implementation order

1. ~~Tests, safe file handling, thread safety, naming~~ (0.2.0).
2. Cleanliness passes 1–8, so every module meets the standard before new
   features land on it.
3. `TIMED_FILE`, which closes the time-rotation gap and proves the theory →
   experiment promotion path, including the thread-safety requirement.
4. `TRACE` and `ASYNC`, which close the context, non-blocking and
   process-safety gaps and unblock LabFrame's GUI profile.
5. Configuration from env or a dict, an exception helper, strict mode, and a
   `"logger"` field in the JSON schema.
6. Then the specialised theories: `PERFORMANCE`, `HTTP`, `SEC`, `DB`.

## Design boundary to preserve

logger-lab should keep owning **composition and presets**: named behaviours,
sensible defaults, a readable way to combine them, and guard rails that keep
compositions from clashing. It should keep returning plain stdlib loggers and
building on stdlib handlers. It should not grow its own logger class or sink
model (that is Loguru's design) or a processor pipeline (structlog's). When
stdlib already has the primitive (queues, timed rotation, filters,
`dictConfig`), logger-lab should wrap it as an experiment rather than
reinvent it.
