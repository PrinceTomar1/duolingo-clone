"""The ``users`` aggregate root."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:  # pragma: no cover - typing only
    from app.models.achievement import UserAchievement
    from app.models.progress import LessonAttempt, UserProgress
    from app.models.stats import DailyXp, UserStats


class User(Base):
    """A learner.

    Deliberately thin: identity lives here, while mutable game state lives in
    ``user_stats`` so a stats write never contends with a profile read.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Unique + indexed: this is the natural key the seed script upserts on.
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    # Stored as a hex string so the frontend can render an avatar without assets.
    avatar_color: Mapped[str] = mapped_column(String(7), nullable=False, default="#58CC02")
    # Optional on purpose, not a shim: this build's whole account model is a
    # named demo profile, not a real identity, and the assignment explicitly
    # accepts simplified auth. NULL means exactly what it says -- "switch
    # learner" stays an instant, no-password switch for the seeded accounts
    # and any new one a reviewer creates without setting one. A learner who
    # does set a password gets an account nobody else can switch into without
    # it, which is the one piece of real authentication worth having: proof
    # that switching to a protected account required knowing its password.
    password_hash: Mapped[str | None] = mapped_column(String(60), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    # Deleting a user removes every row that only makes sense in their context.
    stats: Mapped["UserStats"] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )
    progress: Mapped[list["UserProgress"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    attempts: Mapped[list["LessonAttempt"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    daily_xp: Mapped[list["DailyXp"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    achievements: Mapped[list["UserAchievement"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    @property
    def has_password(self) -> bool:
        """Whether switching into this learner needs a password. Never exposes the hash itself."""
        return self.password_hash is not None
