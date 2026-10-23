"""
Outputs: where feedback goes. A logger holds at most one of each.

* ``CONSOLE`` (`console.py`): Rich by default, or plain text or JSON with a format.
* ``FILE`` (`file.py`): one shared handler per path. Text by default, or JSON with a format.
  Rotation by size (``ROTATING``) and/or schedule (``TIMED``) comes as features.
* ``RELAY`` (`relay.py`): every record to subscriber callbacks (``with_subscriber``).
"""

from logger_lab.outputs.console import CONSOLE_SPEC, LabRichHandler
from logger_lab.outputs.file import FILE_SPEC
from logger_lab.outputs.relay import RELAY_SPEC, RelayHandler

__all__ = ["CONSOLE_SPEC", "FILE_SPEC", "RELAY_SPEC", "LabRichHandler", "RelayHandler"]
