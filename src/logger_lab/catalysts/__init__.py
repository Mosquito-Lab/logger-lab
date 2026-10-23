"""
Catalysts: how every record flows to a logger's outputs. Added with ``with_catalyst(name)``.

* ``ASYNC`` (`asynchronous.py`): the calling thread only queues, and one worker thread writes.

Later: ``TRACE`` and ``HTTP`` (stamp context onto every record on the caller's thread) and
``PROCESS`` (several processes, one writer).
"""

from logger_lab.catalysts.asynchronous import ASYNC_SPEC

__all__ = ["ASYNC_SPEC"]
