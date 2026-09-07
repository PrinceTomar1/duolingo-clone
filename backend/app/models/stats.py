"""Mutable game state: ``user_stats`` and the ``daily_xp`` ledger."""

from datetime import date, datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import settings
from app.core.database import Base

if TYPE_CHECKING:  # pragma: no cover - typing only
    from app.models.user import User


class UserStats(Base):
    """The learner's hearts, currency and streak cache.

    ``user_id`` is both primary key and foreign key: exactly one stats row per
    user, enforced by the schema rather than by application code.
    """

    __tablename__ = "user_stats"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    # Denormalised sum of daily_xp. Kept because the leaderboard sorts on it and
    # re-summing the ledger per row would not scale.
    total_xp: Mapped[int] = mapped_column(Integer, nullable=False, default=0, index=True)
    # Streak fields are a *cache* of what daily_xp implies, refreshed on write
    # and on read; daily_xp remains the source of truth.
    current_streak: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    longest_streak: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_active_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    hearts: Mapped[int] = mapped_column(Integer, nullable=False, default=settings.max_hearts)
    # Anchor for lazy regeneration: hearts owed = elapsed // regen interval.
    hearts_updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    gems: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    daily_goal_xp: Mapped[int] = mapped_column(
        Integer, nullable=False, default=settings.default_daily_goal_xp
    )

    user: Mapped["User"] = relationship(back_populates="stats")


class DailyXp(Base):
    """One row per learner per calendar day with any XP.

    This ledger is the source of truth for both the streak and the daily-goal
    ring. A streak is a property of *which days have rows*, so it can always be
    recomputed; an integer counter cannot be audited or repaired.
    """

    __tablename__ = "daily_xp"
    __table_args__ = (
        UniqueConstraint("user_id", "date", name="uq_user_day"),
        # The streak walk reads a user's recent days in descending date order.
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    xp_earned: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    user: Mapped["User"] = relationship(back_populates="daily_xp")
