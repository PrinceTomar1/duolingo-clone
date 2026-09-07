"""Achievement definitions and the per-user unlock ledger."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:  # pragma: no cover - typing only
    from app.models.user import User


class Achievement(Base):
    """A badge definition, shared by every learner.

    ``code`` is the stable identifier the service layer checks against, so
    renaming a badge's display title never breaks the unlock logic.
    """

    __tablename__ = "achievements"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    icon: Mapped[str] = mapped_column(String(50), nullable=False)
    color_hex: Mapped[str] = mapped_column(String(7), nullable=False)
    # Which learner metric this badge tracks, e.g. "longest_streak". Storing it
    # as data keeps the unlock service a single generic loop rather than a
    # growing if/elif over badge codes.
    metric: Mapped[str] = mapped_column(String(40), nullable=False)
    # The value of that metric at which the badge unlocks.
    target: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    user_achievements: Mapped[list["UserAchievement"]] = relationship(
        back_populates="achievement", cascade="all, delete-orphan"
    )


class UserAchievement(Base):
    """A learner's progress toward one achievement.

    A row exists as soon as there is progress to record; ``unlocked_at`` stays
    NULL until the target is met, which distinguishes "in progress" from "done"
    without a redundant boolean.
    """

    __tablename__ = "user_achievements"
    __table_args__ = (UniqueConstraint("user_id", "achievement_id", name="uq_user_achievement"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    achievement_id: Mapped[int] = mapped_column(
        ForeignKey("achievements.id", ondelete="CASCADE"), index=True, nullable=False
    )
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unlocked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped["User"] = relationship(back_populates="achievements")
    achievement: Mapped["Achievement"] = relationship(back_populates="user_achievements")
