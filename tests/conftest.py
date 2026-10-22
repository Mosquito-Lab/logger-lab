"""
Shared fixtures: every test runs in its own empty folder outside the repository, never
logs to a file inside logger-lab, and leaves no handlers open.
"""

import logging
from pathlib import Path

import pytest

from logger_lab.logging_kernel import SHARED_FILES, clear_handlers

REPO_ROOT = Path(__file__).resolve().parents[1]


def repo_log_files() -> set[Path]:
    """Return every log file inside the repository, ignoring ``.venv`` and ``.git``."""

    return {
        path for path in REPO_ROOT.rglob("*.log*")
        if path.is_file() and not {".venv", ".git"} & set(path.relative_to(REPO_ROOT).parts)
    }


@pytest.fixture(autouse=True, scope="session")
def no_log_files_in_repo():
    """Fail the run if any log file appeared inside the repository while the tests ran."""

    before = repo_log_files()

    yield

    created = repo_log_files() - before

    assert not created, f"tests wrote log files inside the repository: {sorted(map(str, created))}"


@pytest.fixture(autouse=True)
def isolated_cwd(tmp_path, monkeypatch):
    """Run each test inside *tmp_path* so the default ``logs/`` lands outside the repository."""

    monkeypatch.chdir(tmp_path)

    return tmp_path


@pytest.fixture(autouse=True)
def close_lab_handlers():
    """
    Release every handler a test attached, then check two invariants:
    no file handler pointed inside the repo, and the shared file table is empty
    (every file a test opened was released — nothing leaked).
    """

    yield

    inside_repo: list[str] = []

    for logger in list(logging.root.manager.loggerDict.values()):
        if not isinstance(logger, logging.Logger):  # skip PlaceHolder entries
            continue

        for handler in logger.handlers:
            if isinstance(handler, logging.FileHandler) and Path(handler.baseFilename).is_relative_to(REPO_ROOT):
                inside_repo.append(handler.baseFilename)

        clear_handlers(logger)

    leaked = sorted(SHARED_FILES)
    SHARED_FILES.clear()  # keep one leaking test from failing every test after it

    assert not inside_repo, f"a test logged to a file inside the repository: {inside_repo}"
    assert not leaked, f"shared log files were never released: {leaked}"
