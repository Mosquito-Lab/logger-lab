"""
Database theory — query logging (idea stage).

A custom `logging.Filter` plus SQLAlchemy event hooks capturing statement, parameters and
execution time, redacting sensitive bind parameters.  Heavy dependency: an optional extra.

Not registered: selecting it raises `TheoryNotFoundError` until it reaches the trial stage.
"""
