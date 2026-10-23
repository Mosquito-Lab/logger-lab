"""
Trace theory: correlation IDs (idea stage, rank 1).

Correlation-ID middleware sets ``trace_id`` and ``span_id`` in `contextvars` (no
thread-locals), and every record is stamped with them. Then records from one request or
job can be grouped, such as by LabFrame's ``job_id``. Pure stdlib.

Measured constraint: the context must be stamped on the caller's thread. Under ``ASYNC``,
a filter on an output runs on the dispatch worker and sees no context. New threads don't
inherit `contextvars` either, so a job runner must copy the context in
(``contextvars.copy_context().run``).

Kind: open. A feature on an output can't do it, because of the constraint. A logger-level
filter can, and so can a stamp taken while `AsyncHandler` freezes the record.

Not registered: selecting it raises `TheoryNotFoundError` until it reaches the trial stage.
"""
