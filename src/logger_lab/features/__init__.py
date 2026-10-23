"""
Features: extra behavior on an output. Attached with ``with_feature(name, on=..., **options)``.

* Detail (`detail.py`): ``MINIMAL`` and ``VERBOSE``, for console and file, in text and Rich.
* Rotation (`rotation.py`): ``ROTATING`` (by size) and ``TIMED`` (on a schedule), for the file
  only. They combine.

A feature never brings its output with it: queue the output (or use a profile) first.
"""

from logger_lab.features.detail import MINIMAL_SPEC, VERBOSE_SPEC
from logger_lab.features.rotation import ROTATING_SPEC, TIMED_SPEC

__all__ = ["MINIMAL_SPEC", "VERBOSE_SPEC", "ROTATING_SPEC", "TIMED_SPEC"]
