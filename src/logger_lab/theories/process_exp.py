"""
Process theory: several processes, one log file (idea stage, rank 5).

Extends the dispatch queue across processes. Worker processes (multiprocessing pools,
several app instances) send their records to one writer process, which owns the files.
So rotation and shared handlers keep working when more than one process logs. Records
must cross the process boundary pickled, with the message and traceback already turned
into text.

Kind: catalyst, in the ``dispatch`` group alongside ``ASYNC``.

Not registered: selecting it raises `TheoryNotFoundError` until it reaches the trial stage.
"""
