"""Hearts, XP, the daily-XP ledger and streaks.

All of it server-side: the client renders these numbers but never computes them.
The functions that encode a *rule* (heart regeneration, the XP formula, streak
length) are pure and take their inputs explicitly, so the test suite can assert
the rules without a database or a real clock.
"""

from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import clock
from app.core.config import settings
from app.models.stats import DailyXp, UserStats


# --- Hearts -----------------------------------------------------------------


def regenerated_hearts(hearts: int, hearts_updated_at: datetime, at: datetime) -> tuple[int, datetime]:
    """Compute hearts owed since ``hearts_updated_at``.

    Lazy regeneration: rather than a scheduled job ticking every learner's
    hearts every 30 minutes, we store when the counter last moved and derive the
    current value on read. One column instead of a cron, and it stays correct
    even if the server was down for a week.

    The returned timestamp advances only by whole regeneration intervals, so a
    partially-elapsed interval is not silently discarded. Once hearts are full
    the anchor moves to ``at``, so a full heart bar does not bank credit.
    """
    if hearts >= settings.max_hearts:
        return settings.max_hearts, at
    elapsed = at - hearts_updated_at
    if elapsed < timedelta(0):
        return hearts, hearts_updated_at
    interval = timedelta(minutes=settings.heart_regen_minutes)
    earned = int(elapsed // interval)
    if earned <= 0:
        return hearts, hearts_updated_at
    new_hearts = min(settings.max_hearts, hearts + earned)
    if new_hearts >= settings.max_hearts:
        return settings.max_hearts, at
    return new_hearts, hearts_updated_at + interval * earned


def apply_heart_regen(stats: UserStats, at: datetime | None = None) -> UserStats:
    """Fold any owed hearts into the stats row.

    Called at the top of every read and write path that cares about hearts, so
    a learner never sees a stale count.
    """
    moment = at or clock.now()
    stats.hearts, stats.hearts_updated_at = regenerated_hearts(
        stats.hearts, stats.hearts_updated_at, moment
    )
    return stats


def lose_heart(stats: UserStats, at: datetime | None = None) -> UserStats:
    """Deduct one heart for a wrong answer, never below zero.

    The regeneration anchor is reset on the first heart lost from a full bar so
    the next heart is 30 minutes away, not instantly available.
    """
    moment = at or clock.now()
    apply_heart_regen(stats, moment)
    if stats.hearts == settings.max_hearts:
        stats.hearts_updated_at = moment
    stats.hearts = max(0, stats.hearts - 1)
    return stats


def seconds_until_next_heart(stats: UserStats, at: datetime | None = None) -> int | None:
    """Seconds until the next heart lands, or ``None`` when the bar is full."""
    if stats.hearts >= settings.max_hearts:
        return None
    moment = at or clock.now()
    ready_at = stats.hearts_updated_at + timedelta(minutes=settings.heart_regen_minutes)
    return max(0, int((ready_at - moment).total_seconds()))


def refill_hearts(stats: UserStats, at: datetime | None = None) -> bool:
    """Spend gems to top the heart bar back up.

    Returns ``False`` without charging when the learner cannot afford it or is
    already full, so the router can answer 400 rather than silently no-op.
    """
    moment = at or clock.now()
    apply_heart_regen(stats, moment)
    if stats.hearts >= settings.max_hearts or stats.gems < settings.heart_refill_gem_cost:
        return False
    stats.gems -= settings.heart_refill_gem_cost
    stats.hearts = settings.max_hearts
    stats.hearts_updated_at = moment
    return True


# --- XP ---------------------------------------------------------------------


def calculate_lesson_xp(base_xp: int, hearts_lost: int, hearts_remaining: int) -> int:
    """The completion XP formula, in one place.

    base + perfect bonus (no hearts lost) + a bonus per heart still standing.
    Expressed as a pure function so the completion screen, the tests and any
    future "double XP" event all agree on the same arithmetic.
    """
    total = base_xp
    if hearts_lost == 0:
        total += settings.perfect_lesson_bonus_xp
    total += max(0, hearts_remaining) * settings.xp_per_remaining_heart
    return total


# --- Daily XP ledger and streaks -------------------------------------------


def record_daily_xp(db: Session, user_id: int, xp: int, on_day: date | None = None) -> DailyXp:
    """Add XP to today's ledger row, creating it on first activity of the day.

    The UNIQUE(user_id, date) constraint means there can only ever be one row
    per day, so this is an upsert rather than an append.
    """
    day = on_day or clock.today()
    row = db.scalar(select(DailyXp).where(DailyXp.user_id == user_id, DailyXp.date == day))
    if row is None:
        row = DailyXp(user_id=user_id, date=day, xp_earned=0)
        db.add(row)
        # Flushed immediately so a second award in the same transaction finds
        # this row instead of inserting a duplicate and tripping the constraint.
        db.flush()
    row.xp_earned += xp
    return row


def compute_streak(active_days: set[date], today: date) -> int:
    """Count consecutive days of activity ending today or yesterday.

    Derived from the ledger rather than incremented as a counter, so it is
    always reconstructible: a bad deploy that double-counts a day cannot inflate
    a streak, and a support fix means inserting a row rather than guessing a
    number.

    Yesterday is an accepted starting point because a learner who has not
    practised *yet today* has not lost the streak -- they lose it when the day
    rolls over without a row.
    """
    if today in active_days:
        cursor = today
    elif (today - timedelta(days=1)) in active_days:
        cursor = today - timedelta(days=1)
    else:
        return 0
    length = 0
    while cursor in active_days:
        length += 1
        cursor -= timedelta(days=1)
    return length


def active_days(db: Session, user_id: int) -> set[date]:
    """Every calendar day on which the learner earned XP."""
    rows = db.scalars(
        select(DailyXp.date).where(DailyXp.user_id == user_id, DailyXp.xp_earned > 0)
    ).all()
    return set(rows)


def refresh_streak(db: Session, stats: UserStats, today: date | None = None) -> UserStats:
    """Recompute the cached streak fields from the ledger.

    ``current_streak`` and ``longest_streak`` on ``user_stats`` are a cache for
    cheap reads; this is the only function allowed to write them.
    """
    day = today or clock.today()
    days = active_days(db, stats.user_id)
    stats.current_streak = compute_streak(days, day)
    stats.longest_streak = max(stats.longest_streak, stats.current_streak)
    stats.last_active_date = max(days) if days else None
    return stats


def xp_earned_on(db: Session, user_id: int, day: date) -> int:
    """XP banked on a given day -- powers the daily-goal ring."""
    row = db.scalar(select(DailyXp).where(DailyXp.user_id == user_id, DailyXp.date == day))
    return row.xp_earned if row else 0


def xp_earned_since(db: Session, user_id: int, start: date) -> int:
    """XP banked from ``start`` onwards -- powers the weekly leaderboard."""
    rows = db.scalars(
        select(DailyXp.xp_earned).where(DailyXp.user_id == user_id, DailyXp.date >= start)
    ).all()
    return sum(rows)
