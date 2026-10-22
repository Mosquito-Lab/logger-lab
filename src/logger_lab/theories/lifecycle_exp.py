"""
Lifecycle theory — feedback events with a standard shape (idea stage).

A small helper on top of `log_event` that emits the stages of a job as structured
records — ``started``, ``progress`` (with a fraction and an optional message),
``succeeded``, ``failed`` and ``cleared`` — each carrying the job's ID (from ``TRACE``).
Subscribers can then drive a UI from records alone: LabFrame's feedback channels
(panel, problems badges, toasts) could react to these events instead of their own level
conventions, and a console output could render a Rich progress bar from the same events.
This is what makes logger-lab a feedback system rather than only a log sink.

Not registered: selecting it raises `TheoryNotFoundError` until it reaches the trial stage.
"""
