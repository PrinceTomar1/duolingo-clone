"""The single source of "now" for the whole application.

Nothing else calls ``datetime.now()``. Routing every read through here buys two
things: the streak and heart rules become testable without sleeping, and the
debug-only ``/dev/advance-day`` endpoint can move a learner's world forward so
streak behaviour is demonstrable in seconds rather than days.

Two ways to ask for "now" live here, for two different jobs:

- ``now_for``/``today_for`` take the offset as an explicit argument, sourced
  by the caller from that one learner's own ``UserStats.clock_offset_seconds``
  column. This is what every request-handling code path uses. Nothing here is
  shared or mutated, which is exactly what keeps one learner advancing their
  demo day from moving anyone else's -- the earlier design kept that offset in
  a module-level variable, so any visitor calling /dev/advance-day shifted the
  clock for every visitor at once. Persisting it per learner instead of in
  process memory also means a server restart (or a second worker process)
  never resets a learner mid-demo.
- The plain ``now``/``today``/``advance``/``reset`` below are a leftover
  *testing* convenience: several unit tests exercise ``gamification_service``'s
  pure functions directly, with no learner or HTTP request in the picture, and
  use these to simulate a day passing. Nothing reachable from the API depends
  on them any more.
"""

from datetime import date, datetime, timedelta, timezone

_offset = timedelta(0)


def now_for(offset_seconds: int = 0) -> datetime:
    """Current UTC time, shifted by one learner's own persisted offset.

    Returned naive (UTC-based) to match the ``DateTime`` columns, which SQLite
    stores without zone information.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(seconds=offset_seconds)


def today_for(offset_seconds: int = 0) -> date:
    """Current calendar day under one learner's own persisted offset."""
    return now_for(offset_seconds).date()


def now() -> datetime:
    """Real time shifted by the module-level test offset. See the module docstring."""
    return datetime.now(timezone.utc).replace(tzinfo=None) + _offset


def today() -> date:
    """Real calendar day shifted by the module-level test offset."""
    return now().date()


def advance(days: int = 0, minutes: int = 0) -> timedelta:
    """Move the module-level test offset forward. Used only by unit tests."""
    global _offset
    _offset += timedelta(days=days, minutes=minutes)
    return _offset


def reset() -> None:
    """Drop the module-level test offset back to zero. Used only by unit tests."""
    global _offset
    _offset = timedelta(0)


def offset() -> timedelta:
    """The module-level test offset currently applied."""
    return _offset
