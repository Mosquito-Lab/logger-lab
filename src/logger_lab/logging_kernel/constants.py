"""
Default file args, shared by `LabBuilder.with_file_args()` and the file experiments.

The defaults are fixed when those functions are defined, so reassigning one at
runtime changes nothing. To use other values, pass them through `with_file_args()`.
"""

from pathlib import Path

DEFAULT_ENCODING     = "utf-8"          # Log file encoding; override with with_file_args(encoding=...)
DEFAULT_FILENAME     = "app.log"        # Log file name inside the log directory
DEFAULT_LOG_DIR      = Path("logs")     # Log directory, relative to the current working directory
DEFAULT_MAX_BYTES    = 5 * 1024 * 1024  # Size at which a rotating file rolls over: 5 MiB
DEFAULT_BACKUP_COUNT = 3                # Number of rotated backup files to keep
