"""
Theories: building blocks still being researched, at the idea stage. See `TheoryType` and
the theory lifecycle in Standards §3.4.

Each ``*_exp.py`` file holds one idea in its docstring: the mechanism, the purpose and the
likely kind. In roadmap order (Continuation, ``D-20``):

| Rank | Theory          | Likely kind                          |
| ---- | --------------- | ------------------------------------ |
| 1    | ``TRACE``       | open: stamped on the caller's thread |
| 2    | ``LIFECYCLE``   | helper, beside `log_event`           |
| 3    | ``THROTTLE``    | feature, on ``relay``                |
| 4    | ``PERFORMANCE`` | helper (a decorator)                 |
| 5    | ``PROCESS``     | catalyst, in the ``dispatch`` group  |
| 6    | ``HTTP``        | the same as ``TRACE``                |
| 7    | ``SEC``         | output (an audit file)               |
| 8    | ``DB``          | helper, installed on an engine       |

A theory that works is registered with `register_theory` and tried with ``with_theory()``
in a test. A helper is never registered (Standards §3.4).
"""
