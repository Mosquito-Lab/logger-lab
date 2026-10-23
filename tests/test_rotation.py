"""ROTATING and TIMED: the schedule arithmetic, the options, backup naming that never overwrites, and retention."""

import os
import time
from datetime import datetime, time as clock, timezone
from pathlib import Path
from typing import Any

import pytest

from logger_lab import CompositionError, Day, LogFileClashError, Unit, drain, lab
from logger_lab.core.enums import value_of
from logger_lab.logging_kernel import LabFileHandler, TimeRule

THURSDAY = datetime(2026, 10, 22, 15, 30, 45)  # A Thursday afternoon


######################
# The schedule rules #
######################

@pytest.mark.parametrize(("rule", "moment", "start", "boundary"), [
    (TimeRule(every=15, unit="minute"), THURSDAY, datetime(2026, 10, 22, 15, 30), datetime(2026, 10, 22, 15, 45)),
    (TimeRule(unit="hour", at=clock(0, 45)), THURSDAY, datetime(2026, 10, 22, 14, 45), datetime(2026, 10, 22, 15, 45)),
    (TimeRule(every=6, unit="hour"), THURSDAY, datetime(2026, 10, 22, 12), datetime(2026, 10, 22, 18)),
    (TimeRule(), THURSDAY, datetime(2026, 10, 22), datetime(2026, 10, 23)),
    (TimeRule(at=clock(2)), datetime(2026, 10, 22, 1), datetime(2026, 10, 21, 2), datetime(2026, 10, 22, 2)),
    (TimeRule(unit="week"), THURSDAY, datetime(2026, 10, 19), datetime(2026, 10, 26)),
    (TimeRule(unit="week", day="friday"), THURSDAY, datetime(2026, 10, 16), datetime(2026, 10, 23)),
    (TimeRule(unit="week", day="thursday", at=clock(2)), datetime(2026, 10, 22, 1),
     datetime(2026, 10, 15, 2), datetime(2026, 10, 22, 2)),
    (TimeRule(every=2, unit="week", day="monday"), THURSDAY, datetime(2026, 10, 12), datetime(2026, 10, 26)),
    (TimeRule(unit="month"), datetime(2026, 12, 5), datetime(2026, 12, 1), datetime(2027, 1, 1)),
    (TimeRule(unit="month", at=clock(2)), datetime(2026, 10, 1, 1), datetime(2026, 9, 1, 2), datetime(2026, 10, 1, 2)),
    (TimeRule(every=3, unit="month"), datetime(2026, 2, 14), datetime(2026, 1, 1), datetime(2026, 4, 1)),
], ids=["every 15 minutes", "hour at :45", "every 6 hours", "day", "day, before at", "week is Monday",
        "friday", "thursday, before at", "every other monday", "month over new year", "month, before at", "quarter"])
def test_period_start_and_boundary(rule, moment, start, boundary):
    """Each schedule starts its period where expected and ends it at the next one."""

    assert rule.period_start(moment) == start
    assert rule.next_boundary(moment) == boundary


def test_periods_are_anchored_to_the_calendar():
    """A restart never moves the schedule: every moment of a day lands on the same 6-hour grid."""

    rule = TimeRule(every=6, unit="hour")
    starts = {rule.period_start(datetime(2026, 10, 22, hour, minute)) for hour in range(24) for minute in (0, 59)}

    assert sorted(start.hour for start in starts) == [0, 6, 12, 18]

    fortnight = TimeRule(every=2, unit="week", day="monday")

    assert fortnight.period_start(datetime(2026, 10, 13)) == fortnight.period_start(datetime(2026, 10, 25))
    assert fortnight.period_start(datetime(2026, 10, 26)) == datetime(2026, 10, 26)


def test_labels_name_the_period_and_utc_uses_the_utc_clock():
    """Backup labels read as the period they hold. utc=True computes boundaries and labels in UTC."""

    labels = [(TimeRule(unit="minute"), "2026-10-22_15-30"), (TimeRule(unit="hour"), "2026-10-22_15"),
              (TimeRule(), "2026-10-22"), (TimeRule(unit="week"), "2026-10-19"), (TimeRule(unit="month"), "2026-10")]

    for rule, label in labels:
        assert rule.label(rule.period_start(THURSDAY)) == label

    rule = TimeRule(unit="hour", utc=True)
    stamp = datetime(2026, 10, 22, 15, 30, tzinfo=timezone.utc).timestamp()

    assert rule.from_timestamp(stamp) == datetime(2026, 10, 22, 15, 30)
    assert rule.to_timestamp(datetime(2026, 10, 22, 15, 30)) == stamp


###############
# The options #
###############

@pytest.mark.parametrize(("options", "expected"), [
    ({}, TimeRule()),
    ({"unit": "hour"}, TimeRule(every=1, unit="hour")),
    ({"every": 6, "unit": "Hours"}, TimeRule(every=6, unit="hour")),
    ({"every": 6, "unit": Unit.HOUR, "at": ":30"}, TimeRule(every=6, unit="hour", at=clock(0, 30))),
    ({"day": "Friday", "at": "2:30", "utc": True}, TimeRule(unit="week", day="friday", at=clock(2, 30), utc=True)),
    ({"unit": Unit.WEEK, "day": Day.SUNDAY}, TimeRule(unit="week", day="sunday")),
    ({"every": 3, "unit": "months", "at": clock(2)}, TimeRule(every=3, unit="month", at=clock(2))),
], ids=["defaults: daily", "unit alone is every 1", "plural, any case", "Unit member, hour at :MM",
        "day makes it weekly", "Unit and Day members", "quarterly with a time"])
def test_timed_options_are_normalized_on_their_way_to_the_handler(options, expected):
    """Strings or enum members, singular or plural, any case: the handler gets one plain TimeRule."""

    handler = lab().with_output("file").with_feature("TIMED", **options).build("rot.opts").handlers[0]

    assert isinstance(handler, LabFileHandler) and handler.size is None
    assert handler.schedule == expected


def test_every_unit_and_day_works_as_a_member_or_a_string():
    """TS-10: each `Unit` and `Day` member, given as itself or as its lower-case value, gives the same rule."""

    def schedule(**options: Any) -> TimeRule:
        """The rule the file handler gets for these TIMED options."""

        handler = lab().with_output("file").with_feature("TIMED", **options).build("rot.names").handlers[0]
        assert isinstance(handler, LabFileHandler) and handler.schedule is not None

        return handler.schedule

    for unit in Unit:
        name = value_of(unit).lower()

        assert schedule(unit=unit) == schedule(unit=name) == TimeRule(unit=name), unit

    for day in Day:
        name = value_of(day).lower()

        assert schedule(day=day) == schedule(day=name) == TimeRule(unit="week", day=name), day


@pytest.mark.parametrize(("options", "match"), [
    ({"when": "midnight"}, "'TIMED' has no option 'when'; its options: every, unit, day, at, utc"),
    ({"every": "day"}, "every='day': use a whole number, 1 or more"),
    ({"every": 0}, "every=0"),
    ({"unit": "fortnight"},
     r"unit='fortnight': use a Unit member, or one of minute, hour, day, week, month \(plurals too\)"),
    ({"unit": Day.MONDAY}, "use a Unit member"),
    ({"day": "someday"}, "day='someday': use a Day member, or one of monday"),
    ({"unit": "month", "day": "friday"},
     "day= needs a weekly schedule, not unit='month'. Leave unit out, or use unit='week'"),
    ({"unit": "hour", "at": "02:00"}, "for unit='hour', use ':MM'"),
    ({"unit": "hour", "at": ":75"}, "is not a minute past the hour"),
    ({"unit": "minute", "at": ":30"}, "doesn't apply to unit='minute'"),
    ({"at": "2am"}, "at='2am': for unit='day', use 'HH:MM'"),
    ({"at": "25:00"}, r"at='25:00' is not a time of day \(00:00 to 23:59\)"),
    ({"utc": "yes"}, "utc='yes'"),
], ids=["the old when=", "every not a number", "every zero", "unknown unit", "a Day as the unit", "unknown day",
        "day on a monthly unit", "hour at HH:MM", "hour at :75", "minute with at", "at not HH:MM",
        "at out of range", "utc not a bool"])
def test_bad_timed_options_name_the_fix(options, match):
    """Every option is checked at plan time, and the message says what would work."""

    with pytest.raises(CompositionError, match=match):
        lab().with_output("file").with_feature("TIMED", **options).plan()


#################################
# Rollover on a real filesystem #
#################################

def timed_logger(name: str = "rot.timed", backup_count: int = 3, **timed_options: Any):
    """A file logger with TIMED (daily by default), returning the logger and its handler."""

    logger = lab().with_output("file", backup_count=backup_count).with_feature("TIMED", **timed_options).build(name)
    handler = logger.handlers[0]
    assert isinstance(handler, LabFileHandler)

    return logger, handler


def end_period(handler: LabFileHandler, period: datetime) -> None:
    """Pretend *period* is the current file's period and it just ended."""

    handler.period = period
    handler.rollover_at = time.time() - 1  # not 0: Windows can't date 1969


def backups() -> list[str]:
    """The backup file names in ``logs``, sorted."""

    return sorted(path.name for path in Path("logs").glob("app.log.*"))


def test_timed_rollover_names_the_backup_after_its_period(capsys):
    """At the boundary the file becomes ``app.log.<period>`` and a fresh file starts. No WinError 32."""

    logger, handler = timed_logger()

    logger.info("yesterday")
    end_period(handler, datetime(2026, 10, 21))
    logger.info("today")

    assert backups() == ["app.log.2026-10-21"]
    assert "yesterday" in Path("logs/app.log.2026-10-21").read_text(encoding="utf-8")
    assert "today" in Path("logs/app.log").read_text(encoding="utf-8")
    assert handler.rollover_at is not None and handler.rollover_at > time.time()
    assert "PermissionError" not in capsys.readouterr().err


def test_monthly_rollover():
    """unit='month', which the stdlib timed handler can't do."""

    logger, handler = timed_logger(unit="month")

    logger.info("september")
    end_period(handler, datetime(2026, 9, 1))
    logger.info("october")

    assert backups() == ["app.log.2026-09"]


def test_a_backup_is_never_overwritten():
    """If the label is taken (say, the app restarted mid-day), a counter is added. The stdlib would delete it."""

    Path("logs").mkdir()
    Path("logs/app.log.2026-10-21").write_text("earlier piece\n", encoding="utf-8")
    logger, handler = timed_logger()

    logger.info("later piece")
    end_period(handler, datetime(2026, 10, 21))
    logger.info("today")

    assert backups() == ["app.log.2026-10-21", "app.log.2026-10-21.1"]
    assert Path("logs/app.log.2026-10-21").read_text(encoding="utf-8") == "earlier piece\n"


def test_size_and_time_together_count_pieces_within_the_period():
    """ROTATING + TIMED: size rollovers in one day become ``.<day>.1``, ``.<day>.2`` …, and nothing is lost."""

    logger = (
        lab().with_output("file", backup_count=50).with_feature("TIMED").with_feature("ROTATING", max_bytes=200)
        .build("rot.both")
    )
    handler = logger.handlers[0]
    assert isinstance(handler, LabFileHandler) and handler.schedule is not None and handler.period is not None
    today = handler.schedule.label(handler.period)

    for n in range(20):
        logger.info("record %02d padded to make the file grow quickly", n)

    pieces = backups()
    written = "".join(Path("logs", name).read_text(encoding="utf-8") for name in [*pieces, "app.log"])

    assert len(pieces) > 2
    assert pieces == sorted(f"app.log.{today}.{i}" for i in range(1, len(pieces) + 1))
    assert all(f"record {n:02d}" in written for n in range(20))


def test_size_only_keeps_the_numbered_scheme():
    """ROTATING alone: ``app.log.1`` (newest) … ``app.log.N``, at most backup_count of them."""

    logger = lab().with_output("file", backup_count=2).with_feature("ROTATING", max_bytes=100).build("rot.size")

    for n in range(20):
        logger.info("record %02d padded to roll", n)

    assert backups() == ["app.log.1", "app.log.2"]


def test_retention_keeps_the_newest_backups_and_leaves_other_files_alone():
    """backup_count is how many timed backups survive. The oldest periods go first."""

    Path("logs").mkdir()
    Path("logs/app.log.1").write_text("someone else's numbered backup\n", encoding="utf-8")
    logger, handler = timed_logger(backup_count=2)

    for day in (18, 19, 20, 21):
        logger.info("day %d", day)
        end_period(handler, datetime(2026, 10, day))

    logger.info("today")

    assert backups() == ["app.log.1", "app.log.2026-10-20", "app.log.2026-10-21"]


def test_an_existing_file_belongs_to_the_period_it_was_last_written_in():
    """Restarting after a few days rolls the old file into its own day, not today's."""

    Path("logs").mkdir()
    old = Path("logs/app.log")
    old.write_text("from monday\n", encoding="utf-8")
    monday = datetime(2026, 10, 19, 12).timestamp()
    os.utime(old, (monday, monday))

    logger, _ = timed_logger()
    logger.info("now")

    assert backups() == ["app.log.2026-10-19"]
    assert Path("logs/app.log.2026-10-19").read_text(encoding="utf-8") == "from monday\n"


def test_an_idle_period_makes_no_empty_backup():
    """KN-35: a period with nothing written left a 0-byte backup that counted against backup_count."""

    logger, handler = timed_logger(name="rot.idle")

    end_period(handler, datetime(2026, 10, 21))
    logger.info("first record of the day")

    assert backups() == []
    assert handler.rollover_at is not None and handler.rollover_at > time.time()
    assert "first record of the day" in Path("logs/app.log").read_text(encoding="utf-8")


def test_an_oversized_record_never_rotates_an_empty_file():
    """KN-35: a record bigger than max_bytes is written to the empty file, not rotated into an empty backup."""

    logger = lab().with_output("file", backup_count=5).with_feature("ROTATING", max_bytes=10).build("rot.big")

    logger.info("a record far longer than ten bytes")
    logger.info("and another one")

    sizes = {path.name: path.stat().st_size for path in Path("logs").glob("app.log*")}

    assert all(sizes.values()), sizes
    assert sorted(sizes) == ["app.log", "app.log.1"]


########################
# Sharing and dispatch #
########################

def test_timed_files_share_one_handler_and_clash_with_another_rotation():
    """Same path and setup: one handler for both modules. ROTATING on that path is another setup, so it clashes."""

    a = lab().with_output("file").with_feature("TIMED").build("app.a")
    b = lab().with_output("file").with_feature("TIMED").build("app.b")

    assert a.handlers[0] is b.handlers[0]

    clash = r"as FILE\[TEXT\]\+ROTATING, but it is already open as FILE\[TEXT\]\+TIMED"

    with pytest.raises(LogFileClashError, match=clash):
        lab().with_output("file").with_feature("ROTATING").build("app.size")


def test_timed_works_behind_async():
    """TIMED is a feature of the file, so ASYNC dispatches to it like any output."""

    logger = lab().with_output("file").with_feature("TIMED").with_catalyst("ASYNC").build("rot.async")
    logger.warning("queued for the timed file")

    assert drain(5)
    assert "queued for the timed file" in Path("logs/app.log").read_text(encoding="utf-8")


def test_max_bytes_caps_bytes_not_characters():
    """KN-39: the cap counted characters, so non-ASCII text or UTF-16 made files far bigger than max_bytes."""

    for encoding, text in (("utf-8", "é" * 20), ("utf-16", "plain ascii text")):
        logger = (
            lab().with_output("file", filename=f"{encoding}.log", encoding=encoding, backup_count=50)
            .with_feature("MINIMAL").with_feature("ROTATING", max_bytes=90).build(f"rot.{encoding}")
        )

        for _ in range(12):
            logger.info(text)

        sizes = [path.stat().st_size for path in Path("logs").glob(f"{encoding}.log*")]

        assert len(sizes) > 3, encoding
        assert max(sizes) <= 90, (encoding, sizes)
