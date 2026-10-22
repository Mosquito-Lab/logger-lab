"""
Throttle theory — rate limits for live subscribers (idea stage).

Coalesces and rate-limits what reaches a subscriber, so a tight error loop can't flood a
GUI: repeated records collapse into one with a count ("…repeated 120×"), and a
per-subscriber budget (records per second) drops or batches the excess.  It applies to
the ``relay`` channel only — files and consoles keep every record.  It should also give
the dispatch worker some room: a subscriber that gets fewer, larger batches holds the one
worker for less time (see ``KN-19``).

Not registered: selecting it raises `TheoryNotFoundError` until it reaches the trial stage.
"""
