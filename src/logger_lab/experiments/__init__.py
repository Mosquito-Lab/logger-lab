"""
Experiments — each one logging behavior: one handler factory on one channel.

Console: ``standard``, ``verbose``, ``minimalist``.  File: ``file``, ``rotating_file``.
JSON: ``ai``.  Live: ``relay``.  Dispatch: ``async`` (wraps the others).
"""

from logger_lab.experiments.ai            import ai_experiment
from logger_lab.experiments.asynchronous  import async_experiment
from logger_lab.experiments.file          import file_experiment
from logger_lab.experiments.minimalist    import minimalist_experiment
from logger_lab.experiments.relay         import relay_experiment
from logger_lab.experiments.rotating_file import rotating_file_experiment
from logger_lab.experiments.standard      import standard_experiment
from logger_lab.experiments.verbose       import verbose_experiment

__all__ = [
    "standard_experiment",
    "verbose_experiment",
    "minimalist_experiment",
    "file_experiment",
    "rotating_file_experiment",
    "ai_experiment",
    "relay_experiment",
    "async_experiment",
]
