"""
GUI profile — for desktop apps: a rotating log file and live records, off the GUI thread.

Combines ``rotating_file`` (FILE), ``relay`` (LIVE) and ``async`` (DISPATCH).  No console:
windowed builds (``pythonw``, PyInstaller ``--windowed``) have no stdout to write to.
Logging from the GUI thread only queues the record; the dispatch worker writes the file
and calls the subscribers.

Built for LabFrame's feedback channels: pass a Qt signal's ``emit`` as the subscriber and
Qt delivers every record on the GUI thread.  Choose a writable per-user log directory with
`with_file_args(log_dir=...)` — an installed app's working directory may not be writable.
"""

from logging import INFO, Logger

from logger_lab.experiments.asynchronous import async_experiment
from logger_lab.experiments.relay import relay_experiment
from logger_lab.experiments.rotating_file import rotating_file_experiment
from logger_lab.profiles.base import build_profile

GUI_EXPERIMENTS = (rotating_file_experiment, relay_experiment, async_experiment)  # File, live, dispatch


def gui(name: str, level: int = INFO, **kwargs: object) -> Logger:
    """
    Return a logger that writes a rotating file and relays records live, without blocking the caller.

    Experiments applied:
    * ``rotating_file`` — size-rotated log at ``logs/app.log`` (5 MiB, 3 backups).
    * ``relay``         — every record to each subscriber (`LabBuilder.with_subscriber`).
    * ``async``         — both of the above run on the dispatch worker thread.

    Args:
        name:  Logger name, typically ``__name__``.
        level: Logging level.  Defaults to `logging.INFO`.
        **kwargs: File args (``log_dir``, ``filename``, …) and ``subscribers`` forwarded to every experiment.
    Returns:
        A configured `logging.Logger` with ``propagate = False``.
    Example::
        logger = (
            lab().with_profile("gui")
            .with_subscriber(relay.record_logged.emit)
            .with_file_args(log_dir=user_log_dir)
            .build("LabFrame.feedback")
        )
    """

    return build_profile(name, level, *GUI_EXPERIMENTS, **kwargs)
