"""
Security theory: audit stream (idea stage, rank 7).

A separate, append-only audit log that is tamper-evident (hash-chained lines), built on
the shared file handlers. Needs a design for keys and a verification tool.

Kind: output, a file of its own beside the app's log.

Not registered: selecting it raises `TheoryNotFoundError` until it reaches the trial stage.
"""
