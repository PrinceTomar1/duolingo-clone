"""The single source of "now" for the whole application.

Nothing else calls ``datetime.now()``. Routing every read through here buys two
things: the streak and heart rules become testable without sleeping, and the
debug-only ``/dev/advance-day`` endpoint can move the world forward so streak
behaviour is demonstrable in seconds rather than days.

The offset is process-local and deliberately not persisted -- it is a demo aid,
not a feature, and a restart must return the app to real time.
"""

from datetime import date, datetime, timedelta, timezone

_offset = timedelta(0)


def now() -> datetime:
    """Current UTC time, shifted by any simulated offset.

    Returned naive (UTC-based) to match the ``DateTime`` columns, which SQLite
    stores without zone information.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None) + _offset


def today() -> date:
    """Current calendar day under the simulated clock."""
    return now().date()


def advance(days: int = 0, minutes: int = 0) -> timedelta:
    """Move the simulated clock forward and return the new total offset."""
    global _offset
    _offset += timedelta(days=days, minutes=minutes)
    return _offset


def reset() -> None:
    """Drop back to real time. Used by tests and by the dev endpoint."""
    global _offset
    _offset = timedelta(0)


def offset() -> timedelta:
    """The offset currently applied, for reporting back to the caller."""
    return _offset
