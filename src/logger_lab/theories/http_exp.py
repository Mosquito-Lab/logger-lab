"""
HTTP theory: request context (idea stage, rank 6).

Stamps method, path, status and latency from the current request's context onto every
record, for web services. It reads the context ``TRACE`` sets, so ``TRACE``'s constraint
applies: the stamp must be taken on the caller's thread.

Kind: the same as ``TRACE``.

Not registered: selecting it raises `TheoryNotFoundError` until it reaches the trial stage.
"""
