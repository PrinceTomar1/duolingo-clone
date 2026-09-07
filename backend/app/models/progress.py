"""Per-user progress through content: ``user_progress`` and ``lesson_attempts``."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:  # pragma: no cover - typing only
    from app.models.course import Skill
    from app.models.lesson import Lesson
    from app.models.user import User


class UserProgress(Base):
    """A learner's standing in one skill.

    One row per (user, skill) pair, created lazily the first time a learner
    touches the skill. Absence of a row means "untouched", which the path
    service reads as locked-or-available depending on the previous skill.
    """

    __tablename__ = "user_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "skill_id", name="uq_user_skill"),
        # The path endpoint loads every row for one user, so lead with user_id.
        Index("ix_user_progress_user_skill", "user_id", "skill_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    skill_id: Mapped[int] = mapped_column(
        ForeignKey("skills.id", ondelete="CASCADE"), index=True, nullable=False
    )
    # One crown per distinct lesson completed in the skill.
    crowns: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    lessons_completed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_unlocked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    user: Mapped["User"] = relationship(back_populates="progress")
    skill: Mapped["Skill"] = relationship(back_populates="user_progress")


class LessonAttempt(Base):
    """One run through a lesson, open from ``start`` until ``complete``.

    Keeping an attempt row (rather than grading statelessly) is what lets the
    server own hearts and XP: the client holds only an ``attempt_id``, and every
    answer is scored against server state it cannot forge.
    """

    __tablename__ = "lesson_attempts"
    __table_args__ = (
        # Supports "has this user completed this lesson before?" during complete.
        Index("ix_attempt_user_lesson", "user_id", "lesson_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    lesson_id: Mapped[int] = mapped_column(
        ForeignKey("lessons.id", ondelete="CASCADE"), index=True, nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    hearts_lost: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # How many exercises were answered, and how many on the first try -- the
    # completion screen's accuracy card is computed from these.
    exercises_answered: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    xp_earned: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    user: Mapped["User"] = relationship(back_populates="attempts")
    lesson: Mapped["Lesson"] = relationship(back_populates="attempts")
