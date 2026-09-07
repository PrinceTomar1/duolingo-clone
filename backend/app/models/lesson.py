"""Lesson content: ``lessons`` and their ``exercises``."""

from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Enum as SAEnum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import ExerciseType

if TYPE_CHECKING:  # pragma: no cover - typing only
    from app.models.course import Skill
    from app.models.progress import LessonAttempt


class Lesson(Base):
    """An ordered bundle of exercises worth one crown."""

    __tablename__ = "lessons"
    __table_args__ = (UniqueConstraint("skill_id", "order_index", name="uq_lesson_order"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    skill_id: Mapped[int] = mapped_column(
        ForeignKey("skills.id", ondelete="CASCADE"), index=True, nullable=False
    )
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    # Per-lesson override of the base XP award, so a longer lesson can pay more.
    xp_reward: Mapped[int] = mapped_column(Integer, nullable=False, default=10)

    skill: Mapped["Skill"] = relationship(back_populates="lessons")
    exercises: Mapped[list["Exercise"]] = relationship(
        back_populates="lesson",
        cascade="all, delete-orphan",
        order_by="Exercise.order_index",
    )
    attempts: Mapped[list["LessonAttempt"]] = relationship(
        back_populates="lesson", cascade="all, delete-orphan"
    )


class Exercise(Base):
    """A single question.

    The five exercise types have genuinely different shapes -- a word bank has
    tiles, a match-pairs has two columns, a typed answer has neither. Rather
    than five sparse tables or a wide table of mostly-NULL columns, the
    type-specific shape lives in the ``payload`` JSON column and the grader
    dispatches on ``type``. Adding a sixth format becomes a content change plus
    one grader function, not a migration.
    """

    __tablename__ = "exercises"
    __table_args__ = (UniqueConstraint("lesson_id", "order_index", name="uq_exercise_order"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    lesson_id: Mapped[int] = mapped_column(
        ForeignKey("lessons.id", ondelete="CASCADE"), index=True, nullable=False
    )
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    # Stored by name (native_enum=False -> VARCHAR + CHECK) so the value is
    # readable in the database and portable off SQLite.
    type: Mapped[ExerciseType] = mapped_column(
        SAEnum(ExerciseType, native_enum=False, length=32), nullable=False, index=True
    )
    prompt: Mapped[str] = mapped_column(String(255), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    # Never serialised to the client -- ExerciseRead in schemas/lesson.py has no
    # such field, so the omission is structural rather than remembered.
    correct_answer: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    # Optional TTS/audio clip; nullable because most seeded exercises are text.
    audio_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Shown in the red feedback bar to explain a mistake.
    explanation: Mapped[str | None] = mapped_column(String(255), nullable=True)

    lesson: Mapped["Lesson"] = relationship(back_populates="exercises")
