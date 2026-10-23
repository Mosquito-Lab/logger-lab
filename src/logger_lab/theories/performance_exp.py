"""
Performance theory: timing (idea stage, rank 4).

A ``@timed`` decorator factory that emits lifecycle events: ``started``, then
``succeeded`` or ``failed`` with the duration in the JSON standard's ``context`` field.
It depends on ``LIFECYCLE`` for the events and ``TRACE`` for the job ID.

Kind: helper (a decorator).

Selecting it raises `TheoryNotFoundError`. It is never registered, because it is not a
building block. It is tried in tests instead (Standards §3.4).
"""
