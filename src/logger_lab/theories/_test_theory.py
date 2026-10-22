"""
Theory harness — build one theory into a logger and fire a record at every level.

Run it from the repository root, naming the theory by its `TheoryType` value::

    uv run python -m logger_lab.theories._test_theory TIMED_FILE

A placeholder theory (not registered yet) stops with `TheoryNotFoundError`,
which is the expected result until it reaches the trial stage.  Nothing runs
on import.  The leading underscore marks it as the harness, not a theory.
"""

import sys

from logger_lab import lab


def run_theory(theory: str) -> None:
    """Build *theory* at ``DEBUG`` into a ``theory_test`` logger and log one record per level."""

    logger = lab().with_theory(theory).with_level("DEBUG").build("theory_test")

    logger.debug("theory %s: debug", theory)
    logger.info("theory %s: info", theory)
    logger.warning("theory %s: warning", theory)
    logger.error("theory %s: error", theory)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: python -m logger_lab.theories._test_theory <THEORY_NAME>")

    run_theory(sys.argv[1])
