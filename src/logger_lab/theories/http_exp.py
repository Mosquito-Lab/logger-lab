"""
HTTP theory — request context (idea stage).

A custom `logging.Filter` that injects method, path, status and latency from the current
request's context (`contextvars`, from ``TRACE``), for web services.

Not registered: selecting it raises `TheoryNotFoundError` until it reaches the trial stage.
"""
