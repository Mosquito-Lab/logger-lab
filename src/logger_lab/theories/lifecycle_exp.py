"""
Lifecycle theory: feedback events with a standard shape (idea stage, rank 2).

A small helper on top of `log_event` that emits the stages of a job as structured
records: ``started``, ``progress`` (with a fraction and an optional message),
``succeeded``, ``failed`` and ``cleared``. Each carries the job's ID (from ``TRACE``).
Subscribers can then drive a UI from records alone. LabFrame's feedback channels (panel,
problems badges, toasts) could react to these events instead of their own level
conventions. This is what makes logger-lab a feedback system rather than only a log sink.

Kind: helper, beside `log_event`. A Rich progress bar drawn from the same events would be
a separate console feature.

Selecting it raises `TheoryNotFoundError`. It is never registered, because it is not a
building block. It is tried in tests instead (Standards §3.4).
"""
