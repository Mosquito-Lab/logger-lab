"""
Database theory: query logging (idea stage, rank 8).

SQLAlchemy event hooks that log each statement with its parameters and execution time,
redacting sensitive bind parameters. Heavy dependency: an optional extra.

Kind: helper, installed on an engine. The redaction could be a filter it brings along.

Selecting it raises `TheoryNotFoundError`. It is never registered, because it is not a
building block. It is tried in tests instead (Standards §3.4).
"""
