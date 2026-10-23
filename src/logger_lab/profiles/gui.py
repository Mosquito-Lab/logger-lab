"""
GUI profile for desktop apps: a rotating log file and live records, off the GUI thread.

A size-rotated file, the ``relay`` output (records to each subscriber) and the ``ASYNC``
catalyst. No console: windowed builds (``pythonw``, PyInstaller ``--windowed``) have no
stdout or stderr to write to, so a console there would drop every record. Logging from the
GUI thread only queues the record. The dispatch worker writes the file and calls the
subscribers.

Built for LabFrame's feedback channels. Pass a Qt signal's ``emit`` as the subscriber, and
Qt delivers every record on the GUI thread. Choose a writable per-user log directory with
``.with_output("file", log_dir=...)``, because an installed app's working directory may not
be writable.
"""

from typing import TYPE_CHECKING

from logger_lab.core.enums import Catalyst, Feature, Output, ProfileType
from logger_lab.core.specs import ProfileSpec

if TYPE_CHECKING:  # type-only: the builder imports the registry, which imports this module
    from logger_lab.core.builder import LabBuilder


def gui(builder: "LabBuilder") -> "LabBuilder":
    """
    File + ROTATING + relay + ASYNC.

    Example::
        logger = (
            lab().with_profile("gui")
            .with_subscriber(relay.record_logged.emit)
            .with_output("file", log_dir=user_log_dir)
            .build("LabFrame.feedback")
        )
    """

    return (
        builder.with_output(Output.FILE).with_feature(Feature.ROTATING)
        .with_output(Output.RELAY)
        .with_catalyst(Catalyst.ASYNC)
    )


GUI_SPEC = ProfileSpec(member=ProfileType.GUI, recipe=gui, summary="file + ROTATING + relay + ASYNC")
