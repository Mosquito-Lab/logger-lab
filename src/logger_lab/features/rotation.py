"""
Rotation features: keep log files from growing without end. They are for the file output
only, and they combine.

* ``ROTATING``: roll over at ``max_bytes`` (default 5 MiB).
* ``TIMED``: roll over on a schedule, with options in the style of the ``schedule`` package:

  | Option    | Default   | Values                                                              |
  | --------- | --------- | ------------------------------------------------------------------- |
  | ``every`` | ``1``     | How many units make a period, 1 or more                             |
  | ``unit``  | ``"day"`` | A `Unit`, or ``"minute"``, ``"hour"``, ``"day"``, ``"week"``, ``"month"`` (plurals too) |
  | ``day``   | ``None``  | A `Day`, or ``"monday"`` … ``"sunday"``. It makes the unit a week   |
  | ``at``    | ``None``  | ``":MM"`` for an hour; ``"HH:MM"`` for a day, week or month         |
  | ``utc``   | ``False`` | Boundaries and backup names in UTC instead of local time            |

``every`` defaults to 1, so a unit on its own means one of that unit: ``unit="hour"`` rolls
over every hour, and ``day="friday"`` every Friday. Periods are anchored to the calendar, so
a restart never moves the schedule. ``every=6, unit="hours"`` rolls over at 00:00, 06:00,
12:00 and 18:00, and ``every=3, unit="months"`` gives quarters.

The file output's ``backup_count`` (default 3) is how many backups are kept. With ``TIMED``
alone and a daily period, that is the number of days. With both features, a day can hold
several size-capped pieces, so the count covers pieces, not days.

Example::

    lab().with_profile("investigator").with_feature("TIMED", at="02:00")            # daily at 02:00
    lab().with_profile("investigator").with_feature("TIMED", every=6, unit=Unit.HOUR)
    lab().with_profile("investigator").with_feature("TIMED", day=Day.FRIDAY, at="18:00")
    lab().with_output("file").with_feature("ROTATING", max_bytes=10_485_760).with_feature("TIMED", unit="week")
"""

from enum import Enum

from logger_lab.core.enums import Day, Feature, Output, Unit, value_of
from logger_lab.core.specs import FeatureSpec
from logger_lab.logging_kernel.constants import DEFAULT_MAX_BYTES
from logger_lab.logging_kernel.errors import CompositionError
from logger_lab.logging_kernel.rollover import parse_at

FILE_ONLY = frozenset({Output.FILE})  # The rotation features only fit the file output


def check_rotating(options: dict[str, object]) -> dict[str, object]:
    """Require ``max_bytes`` to be a whole number above zero."""

    max_bytes = options["max_bytes"]

    if not isinstance(max_bytes, int) or isinstance(max_bytes, bool) or max_bytes <= 0:
        raise CompositionError(f"'ROTATING' max_bytes={max_bytes!r}: use a whole number of bytes above 0")

    return options


def option_member(enum_type: type[Enum], value: object, option: str, *, plural: bool = False) -> Enum:
    """
    Resolve a ``TIMED`` option to a member of *enum_type*: the member itself, or its value string.

    Strings are case-insensitive. With *plural*, a trailing "s" is allowed (``"hours"``).

    Raises:
        `CompositionError`: For anything else, listing the valid values.
    Example::
        option_member(Unit, "Hours", "unit", plural=True)   # Unit.HOUR
    """

    if isinstance(value, enum_type):
        return value

    if isinstance(value, str):
        text = value.strip().upper()

        if plural and text.endswith("S"):
            text = text[:-1]

        for member in enum_type:
            if value_of(member) == text:
                return member

    names = ", ".join(value_of(member).lower() for member in enum_type)
    extra = " (plurals too)" if plural else ""
    raise CompositionError(f"'TIMED' {option}={value!r}: use a {enum_type.__name__} member, or one of {names}{extra}")


def check_timed(options: dict[str, object]) -> dict[str, object]:
    """
    Check and normalize the ``TIMED`` options.

    ``unit`` and ``day`` may be `Unit` and `Day` members or their names as strings. Both
    become lower-case strings for the file handler. The unit defaults to a week when ``day``
    is given, otherwise to a day. ``every`` defaults to 1, so a unit alone means one of it.
    ``at`` is parsed for the unit.

    Returns:
        The options with ``every``, ``unit``, ``day`` and ``at`` normalized.
    Raises:
        `CompositionError`: For a value or combination that can't work. The message names it.
    Example::
        check_timed({"every": 6, "unit": "Hours", "day": None, "at": ":30", "utc": False})
        # {"every": 6, "unit": "hour", "day": None, "at": time(0, 30), "utc": False}
    """

    every = options["every"]

    if not isinstance(every, int) or isinstance(every, bool) or every < 1:
        raise CompositionError(f"'TIMED' every={every!r}: use a whole number, 1 or more")

    day = None if options["day"] is None else option_member(Day, options["day"], "day")
    given = options["unit"]

    if given is None:
        unit = Unit.WEEK if day is not None else Unit.DAY
    else:
        unit = option_member(Unit, given, "unit", plural=True)

    unit_name = value_of(unit).lower()

    if day is not None and unit is not Unit.WEEK:
        raise CompositionError(f"'TIMED' day= needs a weekly schedule, not unit={unit_name!r}. "
                               f"Leave unit out, or use unit='week'")

    try:
        at = parse_at(options["at"], unit_name)

    except ValueError as err:
        raise CompositionError(f"'TIMED' {err}") from err

    if not isinstance(options["utc"], bool):
        raise CompositionError(f"'TIMED' utc={options['utc']!r}: use True or False")

    day_name = None if day is None else value_of(day).lower()

    return {**options, "every": every, "unit": unit_name, "day": day_name, "at": at}


ROTATING_SPEC = FeatureSpec(
    member=Feature.ROTATING, fits=FILE_ONLY,
    options={"max_bytes": DEFAULT_MAX_BYTES}, check=check_rotating
)
TIMED_SPEC = FeatureSpec(
    member=Feature.TIMED, fits=FILE_ONLY,
    options={"every": 1, "unit": None, "day": None, "at": None, "utc": False}, check=check_timed
)
