"""
File output: feedback for whoever reads the logs later.

There is one `LabFileHandler` per path for the whole process. Every logger writing to the
same file shares it (see `share_file_handler()`). So modules can log to one ``app.log`` at
their own levels, and rotation works on Windows. Plain text by default, and ``JSON`` writes
JSON lines.

Features:

* ``ROTATING``: roll over at ``max_bytes``;
* ``TIMED``: roll over on a schedule (``every=``, ``unit=``, ``day=``, ``at=``, ``utc=``);
* both together: daily *and* size-capped, with backups named ``app.log.2026-10-22.1``, ``.2`` …;
* ``MINIMAL`` / ``VERBOSE``: less or more detail per line (text only).

Options: ``log_dir="logs"``, ``filename="app.log"``, ``encoding="utf-8"`` and
``backup_count=3``. The last one is how many rotated backups to keep, for either rotation
feature. The directory is created on build.
"""

from logging import NOTSET, Handler

from logger_lab.core.enums import Feature, Format, Output, value_of
from logger_lab.core.specs import OutputPlan, OutputSpec
from logger_lab.logging_kernel.constants import (
    DEFAULT_BACKUP_COUNT, DEFAULT_ENCODING, DEFAULT_FILENAME, DEFAULT_LOG_DIR,
)
from logger_lab.logging_kernel.errors import CompositionError
from logger_lab.logging_kernel.formatters import JSONFormatter, text_formatter
from logger_lab.logging_kernel.handlers import LabFileHandler, configure_handler, get_log_dir, share_file_handler
from logger_lab.logging_kernel.rollover import SizeRule, TimeRule


def check_file(plan: OutputPlan) -> None:
    """Reject a rotating file that keeps no backups, and a non-integer or negative backup count."""

    backup_count = plan.options["backup_count"]

    if not isinstance(backup_count, int) or isinstance(backup_count, bool) or backup_count < 0:
        raise CompositionError(f"file backup_count={backup_count!r}: use a whole number, 0 or more")

    rotations = {Feature.ROTATING, Feature.TIMED} & plan.features.keys()  # The rotation features on this file

    if rotations and backup_count == 0:
        names = " and ".join(sorted(f"'{value_of(feature)}'" for feature in rotations))
        raise CompositionError(f"{names} need backup_count of 1 or more to have somewhere to roll over to")


def build_file(plan: OutputPlan) -> list[Handler]:
    """
    Return the shared file handler for *plan*: its path, format, detail and rollover rules.

    Args:
        plan: The file's options, features and format, from the builder.
    Returns:
        A single-element list with the shared `LabFileHandler`.
    Raises:
        `LogFileClashError`: If another logger has this file open with a different format or rotation.
    Example::
        lab().with_output("file", log_dir="run").with_feature("ROTATING", max_bytes=1_048_576).build(__name__)
    """

    options = plan.options
    log_path = get_log_dir(str(options["log_dir"])) / str(options["filename"])
    encoding = str(options["encoding"])
    backup_count = int(options["backup_count"])  # pyrefly: ignore[bad-argument-type]

    # The options were checked by the specs, so they convert as they are.
    rotating = plan.features.get(Feature.ROTATING)
    timed = plan.features.get(Feature.TIMED)
    size = SizeRule(int(rotating["max_bytes"])) if rotating is not None else None  # pyrefly: ignore[bad-argument-type]
    schedule = TimeRule(**timed) if timed is not None else None  # pyrefly: ignore[bad-argument-type]

    assert plan.format is not None  # the file always has one (TEXT by default)
    formatter = JSONFormatter() if plan.format is Format.JSON else text_formatter(plan.detail)

    # Another logger shares the file only if its kind matches exactly and its settings agree.
    kind = f"FILE[{value_of(plan.format)}]"
    settings: dict[str, object] = {"encoding": encoding, "backup_count": backup_count, "detail": plan.detail}

    if size is not None:
        kind += f"+{value_of(Feature.ROTATING)}"
        settings["max_bytes"] = size.max_bytes

    if schedule is not None:
        kind += f"+{value_of(Feature.TIMED)}"
        settings.update(every=schedule.every, unit=schedule.unit, day=schedule.day, at=schedule.at, utc=schedule.utc)

    def open_handler() -> LabFileHandler:
        """Open the file's handler. Only called if no logger has the file open yet."""

        handler = LabFileHandler(log_path, encoding=encoding, backup_count=backup_count, size=size, schedule=schedule)

        return configure_handler(handler, NOTSET, formatter)

    return [share_file_handler(log_path, kind=kind, settings=settings, open_handler=open_handler,
                               logger_name=plan.logger_name)]


FILE_SPEC = OutputSpec(
    member=Output.FILE,
    build=build_file,
    options={"log_dir": DEFAULT_LOG_DIR, "filename": DEFAULT_FILENAME, "encoding": DEFAULT_ENCODING,
             "backup_count": DEFAULT_BACKUP_COUNT},
    formats=frozenset({Format.TEXT, Format.JSON}),
    default_format=Format.TEXT,
    check=check_file,
)
