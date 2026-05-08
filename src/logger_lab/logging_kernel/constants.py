from pathlib import Path

# Default file encoding. This one shouldn't be changed anyhow.
DEFAULT_ENCODING     = 'utf-8'

# Default log file name written inside the log directory.
DEFAULT_FILENAME     = 'app.log'

# Default log directory — relative to the current working directory.
DEFAULT_LOG_DIR      = Path('logs')

# Default maximum file size before rotation: 5 MiB.
DEFAULT_MAX_BYTES    = 5 * 1024 * 1024

# Default number of rotated backup files to retain.
DEFAULT_BACKUP_COUNT = 3
