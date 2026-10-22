"""
Process theory — several processes, one log file (idea stage).

Extends the dispatch queue across processes: worker processes (multiprocessing pools,
several app instances) send their records to one writer process, which owns the files,
so rotation and shared handlers keep working when more than one process logs.  Records
must cross the process boundary pickled, with the message and traceback already turned
into text.  Likely a dispatcher (``DISPATCH`` channel) alongside ``async``.

Not registered: selecting it raises `TheoryNotFoundError` until it reaches the trial stage.
"""
