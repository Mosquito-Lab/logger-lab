"""
Performance theory — timing (idea stage).

A ``@timed`` decorator factory that logs start, end and duration through `log_event`,
filling the JSON standard's ``context`` field.  Builds on ``TRACE`` context if it exists.

Not registered: selecting it raises `TheoryNotFoundError` until it reaches the trial stage.
"""
