import logging

from logging import Logger
from pathlib import Path
from datetime import datetime
from rich.logging import RichHandler

# LOGGING

# Dynamic logger that looks nice
def rich_config(name: str, log_file: str = None, level=logging.INFO) -> Logger:
    """
    Set up a logger with rich console output and file logging

    Args:
        name: Logger name (usually __name__)
        log_file: Optional specific log file name
        level: Logging level
    Returns:
        Configured logger
    """

    # Create logs directory
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # File handler (no colors in file)
    if log_file is None:
        log_file = f"{name.split('.')[-1]}_{datetime.now().strftime('%Y%m%d')}.log"

    file_handler = logging.FileHandler(log_dir / log_file, mode='a', encoding='utf-8')
    file_handler.setLevel(level)

    # Rich console handler with colors
    console_handler = RichHandler(
        rich_tracebacks=True,
        markup=True,
        show_time=True,
        show_level=True,
        show_path=False)
    console_handler.setLevel(level)

    # Detailed formatter for file
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s : %(funcName)s : %(lineno)d - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')

    # Simple formatter for rich console (rich handles the rest)
    console_formatter = logging.Formatter(
        '%(message)s',
        datefmt='[%X]')

    file_handler.setFormatter(file_formatter)
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
