"""
Rollover rules for the file output: by size (``ROTATING``), on a schedule (``TIMED``), or both.

The schedule options follow the popular ``schedule`` package, as keyword arguments:
``every=6, unit="hours"`` is ``schedule.every(6).hours``, and ``day="friday", at="18:00"``
is ``schedule.every().friday.at("18:00")``. ``every`` defaults to 1, so ``unit="hour"`` on
its own means every hour, like ``schedule.every().hour``. Unlike ``schedule``, there is a ``month`` unit,
and periods are anchored to the calendar instead of to when the app started. So
``every=6, unit="hours"`` always rolls over at 00:00, 06:00, 12:00 and 18:00, and a restart
never moves the schedule.

The time arithmetic lives here rather than in `TimedRotatingFileHandler`, for two reasons:

* the stdlib has no monthly rotation;
* the stdlib *deletes* an existing backup with the same date name. A size rollover in the
  middle of a day would silently destroy the earlier backup.

Periods are computed on wall-clock datetimes: local time by default, UTC with ``utc=True``.
So "every day at 02:00" stays at 02:00 when the clocks change. One exception: an ``at=``
inside the hour the clocks skip in spring rolls over an hour late that day (Python's rule
for skipped times, PEP 495). Use ``utc=True`` to avoid it.
"""

import re
from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone

UNITS = ("minute", "hour", "day", "week", "month")  # The units a TimeRule knows (the Unit enum, lower-case)
DAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")  # In datetime.weekday() order
STEPS = {"minute": timedelta(minutes=1), "hour": timedelta(hours=1), "day": timedelta(days=1),
         "week": timedelta(weeks=1)}  # One unit's length; a month has none, so it is counted in months
ANCHOR = datetime(1970, 1, 5)  # A Monday at midnight. Every period counts from here, so restarts don't move it
LABEL_FORMATS = {"minute": "%Y-%m-%d_%H-%M", "hour": "%Y-%m-%d_%H", "month": "%Y-%m"}  # The rest use "%Y-%m-%d"
LABEL_PATTERN = re.compile(r"^(\d{4}-\d{2}(?:-\d{2}(?:_\d{2}(?:-\d{2})?)?)?)(?:\.(\d+))?$")  # label[.N]
MIDNIGHT = time(0, 0)  # When a period starts if at= isn't given


@dataclass(frozen=True)
class SizeRule:
    """Roll the file over once writing a record would reach *max_bytes*."""

    max_bytes: int


@dataclass(frozen=True)
class TimeRule:
    """
    Roll the file over at the start of every period.

    The ``TIMED`` feature checks the options and turns them into these plain, lower-case
    fields (the `Unit` and `Day` enums live above this layer).

    Args:
        every:   How many units make a period, 1 or more. With the default, 1, a period is
                 one unit: ``unit="hour"`` means every hour.
        unit:    ``"minute"``, ``"hour"``, ``"day"``, ``"week"`` or ``"month"``.
        day:     For a week: the day it starts on, ``"monday"`` (default) to ``"sunday"``.
        at:      When in its first unit a period starts. For an hour, only the minute counts
                 (``":30"``). For a day, week or month, it is the time of day (``"02:00"``).
        utc:     Use UTC instead of local time for the boundaries and the backup names.
    Example::
        TimeRule(every=2, unit="week", day="monday", at=time(2, 0))   # every other Monday at 02:00
    """

    every: int = 1
    unit: str = "day"
    day: str | None = None
    at: time | None = None
    utc: bool = False

    def now(self) -> datetime:
        """The current wall-clock time in this rule's clock (naive, local or UTC)."""

        return datetime.now(timezone.utc).replace(tzinfo=None) if self.utc else datetime.now()

    def from_timestamp(self, timestamp: float) -> datetime:
        """A POSIX timestamp as a naive datetime in this rule's clock."""

        if self.utc:
            return datetime.fromtimestamp(timestamp, timezone.utc).replace(tzinfo=None)

        return datetime.fromtimestamp(timestamp)

    def to_timestamp(self, moment: datetime) -> float:
        """A naive datetime in this rule's clock as a POSIX timestamp."""

        return moment.replace(tzinfo=timezone.utc).timestamp() if self.utc else moment.timestamp()

    def period_start(self, moment: datetime) -> datetime:
        """
        Return the start of the period that contains *moment*.

        Periods are whole multiples of *every* units, counted from the calendar: from
        `ANCHOR` for minutes to weeks, and from January for months. So ``every=3`` months
        gives quarters, and ``every=2`` weeks keeps the same Mondays across restarts.
        """

        at = self.at or MIDNIGHT

        if self.unit == "month":
            start = moment.replace(day=1, hour=at.hour, minute=at.minute, second=0, microsecond=0)

            if start > moment:
                start = shift_months(start, -1)

            index = start.year * 12 + start.month - 1

            return shift_months(start, -(index % self.every))

        step = STEPS[self.unit] * self.every
        anchor = ANCHOR + self.offset(at)

        return anchor + step * ((moment - anchor) // step)

    def offset(self, at: time) -> timedelta:
        """How far after `ANCHOR` the first period starts: the day of the week, then *at*."""

        if self.unit == "minute":
            return timedelta()

        if self.unit == "hour":
            return timedelta(minutes=at.minute)

        days = DAYS.index(self.day or "monday") if self.unit == "week" else 0

        return timedelta(days=days, hours=at.hour, minutes=at.minute)

    def next_boundary(self, moment: datetime) -> datetime:
        """Return when the period containing *moment* ends. That is the next rollover."""

        start = self.period_start(moment)

        if self.unit == "month":
            return shift_months(start, self.every)

        return start + STEPS[self.unit] * self.every

    def label(self, period_start: datetime) -> str:
        """The backup-name label for the period starting at *period_start*, e.g. ``"2026-10-22"``."""

        return period_start.strftime(LABEL_FORMATS.get(self.unit, "%Y-%m-%d"))


def shift_months(moment: datetime, months: int) -> datetime:
    """Return *moment* (a 1st-of-month datetime) moved by *months*."""

    index = moment.year * 12 + moment.month - 1 + months

    return moment.replace(year=index // 12, month=index % 12 + 1)


def parse_at(value: object, unit: str) -> time | None:
    """
    Parse an ``at=`` value for *unit*.

    For an hour, ``at`` is ``":MM"``: the minute past each hour. For a day, week or month,
    it is ``"HH:MM"`` (``"2:30"`` works too) or a `datetime.time`. A minute takes no ``at``.

    Returns:
        The parsed time (for an hour, ``time(0, MM)``), or ``None`` if *value* is ``None``.
    Raises:
        `ValueError`: For a value that doesn't fit *unit*, including an hour or minute out
        of range. The caller turns it into a `CompositionError`.
    Example::
        parse_at(":30", "hour")      # time(0, 30)
        parse_at("02:00", "day")     # time(2, 0)
    """

    if value is None:
        return None

    if unit == "minute":
        raise ValueError(f"at={value!r} doesn't apply to unit='minute'")

    if unit == "hour":
        match = re.fullmatch(r":(\d{2})", str(value).strip())

        if match is None:
            raise ValueError(f"at={value!r}: for unit='hour', use ':MM', such as ':30'")

        minute = int(match.group(1))

        if minute > 59:
            raise ValueError(f"at={value!r} is not a minute past the hour (:00 to :59)")

        return time(0, minute)

    if isinstance(value, time):
        return value

    match = re.fullmatch(r"(\d{1,2}):(\d{2})", str(value).strip())

    if match is None:
        raise ValueError(f"at={value!r}: for unit={unit!r}, use 'HH:MM', such as '02:00'")

    hour, minute = int(match.group(1)), int(match.group(2))

    if hour > 23 or minute > 59:
        raise ValueError(f"at={value!r} is not a time of day (00:00 to 23:59)")

    return time(hour, minute)


def backup_sort_key(suffix: str) -> tuple[str, int] | None:
    """Sort key for a timed backup suffix ``label[.N]``, or ``None`` if it isn't one of ours."""

    match = LABEL_PATTERN.match(suffix)

    if match is None:
        return None

    return match.group(1), int(match.group(2) or 0)
