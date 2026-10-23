"""
Throttle theory: rate limits for live subscribers (idea stage, rank 3).

Coalesces and rate-limits what reaches a subscriber, so a tight error loop can't flood a
GUI. Repeated records collapse into one with a count ("…repeated 120×"). A per-subscriber
budget (records per second) drops or batches the excess. Files and consoles keep every
record. It should also give the dispatch worker some room. A subscriber that gets fewer,
larger batches holds the one worker for less time (see ``KN-19``).

Kind: feature, on the ``relay`` output only.

Not registered: selecting it raises `TheoryNotFoundError` until it reaches the trial stage.
"""
