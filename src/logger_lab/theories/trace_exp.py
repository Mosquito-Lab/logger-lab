"""
Trace theory — correlation IDs (idea stage).

A custom `logging.Filter` plus correlation-ID middleware that stamps ``trace_id`` and
``span_id`` onto every record from `contextvars` (no thread-locals), so records from one
request or job can be grouped — e.g. LabFrame's ``job_id``.  Pure stdlib.

Not registered: selecting it raises `TheoryNotFoundError` until it reaches the trial stage.
"""
