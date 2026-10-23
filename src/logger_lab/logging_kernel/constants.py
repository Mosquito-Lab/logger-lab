"""
Defaults for the file output's and the rotation features' options.

They are read when the specs are defined, so reassigning one at runtime changes
nothing. To use other values, pass them as options: ``with_output("file", log_dir=...)``,
``with_feature("ROTATING", max_bytes=...)``.
"""

from pathlib import Path

DEFAULT_ENCODING     = "utf-8"          # Log file encoding; override with with_output("file", encoding=...)
DEFAULT_FILENAME     = "app.log"        # Log file name inside the log directory
DEFAULT_LOG_DIR      = Path("logs")     # Log directory, relative to the current working directory
DEFAULT_MAX_BYTES    = 5 * 1024 * 1024  # Size at which a rotating file rolls over: 5 MiB
DEFAULT_BACKUP_COUNT = 3                # Number of rotated backup files to keep (both rotation features)
