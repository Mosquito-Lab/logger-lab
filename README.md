# 🧪 logger-lab

> Logging, reimagined as a system.

`logger-lab` is a composable Python logging toolkit built around a simple idea:

**logging should be modular, readable, and adaptable — for both humans and machines.**

Instead of writing repetitive logging setup, you select from **experiments**, apply **profiles**, or compose your own logger by assembling them like a system.

---

## 🚀 Installation

```bash
pip install logger-lab
```

---

## ⚡ Quick Start

```python
from logger_lab import get_logger, ProfileType

logger = get_logger(__name__, profile=ProfileType.INVESTIGATOR)

logger.info("System online")
logger.debug("Inspecting state")
logger.error("Something broke")
```

---

## 🧪 Experiments

Experiments are **atomic logging behaviours** — pure functions that return a list of configured handlers.

Each experiment controls exactly one thing: how logs are formatted and where they go.

| Experiment      | Handler                  | Description                                       |
|-----------------|--------------------------|---------------------------------------------------|
| `standard`      | `RichHandler`            | Colourised console output with traceback support  |
| `minimalist`    | `StreamHandler`          | Plain `LEVEL: message` — warnings only by default |
| `verbose`       | `StreamHandler`          | Full context: timestamp, module, function, line   |
| `file`          | `FileHandler`            | Persistent plain-text log at `logs/app.log`       |
| `rotating_file` | `RotatingFileHandler`    | Auto-rotates at 5 MiB, keeps 3 backups            |
| `ai`            | `StreamHandler` (stderr) | Structured JSON — Mosquito Lab Standard v1        |

### Using a single experiment

```python
from logger_lab import get_logger, ExperimentType

logger = get_logger(__name__, experiment=ExperimentType.MINIMALIST)
logger.info("Ready")
```

---

## 🧫 Profiles

Profiles are **prebuilt combinations of experiments** tuned for common use cases.

| Profile               | Experiments                          | Use case                             |
|-----------------------|--------------------------------------|--------------------------------------|
| `observer`            | `minimalist`                         | Production — warnings and above only |
| `investigator`        | `standard` + `file`                  | Development — Rich console + disk    |
| `conspiracy_theorist` | `verbose` + `file` + `rotating_file` | Deep archival — nothing missed       |
| `ai_agent`            | `ai`                                 | Structured JSON for pipelines        |

```python
from logger_lab import get_logger, ProfileType

payload = "super dangerous and malicious payload!"

logger = get_logger(__name__, profile=ProfileType.CONSPIRATOR)
logger.debug("Payload received: %s", payload)
logger.error("Unexpected response", exc_info=True)
```

Brushing up the logic for using strings and not enums:

```python
from logger_lab import get_logger

logger = get_logger(__name__, profile="CONSPIRACY_THEORIST")
```

---

## 🧬 Custom Composition

For full control, build your logger like a system:

```python
from logger_lab import lab, ExperimentType

logger = (
    lab()
    .with_experiment(ExperimentType.MINIMALIST)
    .with_experiment(ExperimentType.FILE)
    .with_level("DEBUG")
    .build(__name__)
)
```

Mix a profile with additional experiments:

```python
from logger_lab import lab, ExperimentType, ProfileType

logger = (
    lab()
    .with_profile(ProfileType.INVESTIGATOR)
    .with_experiment(ExperimentType.AI)
    .with_level("INFO")
    .build(__name__)
)
```

---

## 🤖 AI Logging (Core Feature)

`logger-lab` includes a structured logging format designed for AI systems.

Logs become **machine-readable events**, not just text.

### Example Output

```json
{
  "timestamp": "2026-05-05T12:00:00+00:00",
  "level": "INFO",
  "message": "User logged in",
  "source": {
    "module": "auth",
    "function": "login",
    "line": 88
  },
  "extra": {
    "event": "user_login",
    "context": { "user_id": 42 },
    "tags": ["auth"]
  }
}
```

### Usage

Use `log_event()` — it constructs a fresh `extra` dict on every call so successive calls never share mutable state:

```python
from logger_lab import get_logger, log_event, ProfileType
import logging

logger = get_logger(__name__, profile=ProfileType.AGENT)

log_event(
    logger, logging.INFO, "User logged in",
    event="user_login",
    context={"user_id": 42},
    tags=["auth"],
)
```

---

## 🚨 Error Handling

All exceptions inherit from `LabError` so you can catch broadly or precisely.

```
LabError
├── LabRegistryError
│   ├── ExperimentNotFoundError    — valid ExperimentType not registered
│   ├── ProfileNotFoundError       — valid ProfileType not registered
│   ├── InvalidExperimentName      — unrecognised experiment string
│   └── InvalidProfileName         — unrecognised profile string
├── LabConfigurationError
│   ├── InvalidLevelError          — bad level string or int
│   ├── HandlerConfigurationError  — handler failed to initialise
│   │   └── LogDirectoryError      — log directory mkdir/access failure
│   ├── ExperimentRegistrationError — callable doesn't satisfy ExperimentFactory
│   └── ProfileRegistrationError    — callable doesn't satisfy ProfileFactory
└── BuilderError                   — build() called with nothing queued
```

### Broad catch

```python
from logger_lab import get_logger, LabError

try:
    logger = get_logger(__name__, profile="typo")
except LabError as exc:
    print(f"logger-lab error: {exc}")
```

### Precise catch

```python
from logger_lab import get_logger, InvalidProfileName, BuilderError

try:
    logger = get_logger(__name__, profile="typo")
except InvalidProfileName as exc:
    print(f"Unknown profile: {exc}")   # lists valid names in the message
except BuilderError as exc:
    print(f"Builder misconfigured: {exc}")
```

---

## 🏗️ Architecture

```
logger_lab/
├── __init__.py           ← public API: get_logger(), lab(), log_event()
├── core/
│   ├── enums.py          ← ExperimentType, ProfileType
│   ├── registry.py       ← EXPERIMENTS + PROFILES dicts, validated registration
│   └── builder.py        ← LabBuilder fluent interface + lab() factory
├── experiments/          ← atomic handler factories (level) → list[Handler]
│   ├── standard.py       ← RichHandler
│   ├── minimalist.py     ← StreamHandler, warnings only
│   ├── verbose.py        ← StreamHandler, full context
│   ├── file.py           ← FileHandler
│   ├── rotating_file.py  ← RotatingFileHandler
│   └── ai.py             ← StreamHandler + JSONFormatter
├── profiles/             ← prebuilt logger configurations
│   ├── _base.py          ← _build_profile() shared skeleton
│   ├── observer.py
│   ├── investigator.py
│   ├── conspiracy_theorist.py
│   └── ai_agent.py
├── theories/             ← explore different theories to invent new experiments
│   ├── _test_theory.py   ← test a theory (even I don't know what'll happen)
│   ├── my_stuff_exp.py
│   └── your_stuff_exp.py
└── logging_kernel/       ← shared infrastructure
    ├── errors.py         ← full exception hierarchy
    ├── formatters.py     ← JSONFormatter, log_event(), formatter factories
    └── handlers.py       ← _configure_handler(), normalise_*(), get_log_dir()
```

---

## 🧬 Philosophy

`logger-lab` is built on three principles:

1. **Modularity** — Logging behaviour should be reusable and composable.
2. **Clarity** — Logs should be easy to read and understand.
3. **Structure** — Logs should be usable as data, not just text.

> Logs are not just for debugging.
> They are inputs for analysis, automation, and intelligence.

---

## 🧪 Experimental Features

Some features live in the experimental zone (theories):

```python
from logger_lab import get_logger
from logger_lab.core.enums import TheoryType

# THEORIES (single handler factories):
theory_logger = get_logger(name="doom", theory=TheoryType.TIMED_FILE)

```

These are unstable and may change.

---

## 🤝 Contributing

Contributions are welcome.

### Adding a new experiment

1. Create `logger_lab/theories/your_name_exp.py`
2. Define `your_name_experiment(level: int = DEBUG, **kwargs) -> list[logging.Handler]`
3. Add the enum value to `TheoryType` in `core/enums.py`
4. Manually register it in the THEORIES registry
5. Test in `_test_theory.py`
6. Document its purpose and behaviour
7. After review, the Lab will add it to experiments logic

### Adding a new profile

Currently just on a suggestion basis. I don't know about adding experimental logic for a profile

---

## 🧭 Roadmap

* [ ] More experiments (`async`, `http`, `db`, `performance`)
* [ ] Advanced profiles
* [ ] AI-assisted debugging tools
* [ ] Distributed tracing support
* [ ] `py.typed` marker + full type stub coverage

---

## 🧑‍💻 Author

**Mosquito Lab (Cyber-Smoke)**
📧 [mosquitolab2024@protonmail.com](mailto:mosquitolab2024@protonmail.com)
🔗 [github.com/Mosquito-Lab/logger-lab](https://github.com/Mosquito-Lab/logger-lab)

---

## 📄 License

MIT LICENSE

---

## 🌱 Status

`v0.1.0` — Active development. New experiments, profiles, and capabilities are being added continuously.

## Bugs
Still handling the file stuff but it works. Just handling the defaults and placing the file logic is left.