"""Course content hierarchy: ``courses`` -> ``units`` -> ``skills``."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:  # pragma: no cover - typing only
    from app.models.lesson import Lesson
    from app.models.progress import UserProgress


class Course(Base):
    """A language pairing, e.g. English -> Spanish."""

    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    from_language: Mapped[str] = mapped_column(String(50), nullable=False)
    to_language: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)

    units: Mapped[list["Unit"]] = relationship(
        back_populates="course",
        cascade="all, delete-orphan",
        order_by="Unit.order_index",
    )


class Unit(Base):
    """A themed section of a course, rendered as a coloured header bar."""

    __tablename__ = "units"
    # Two units in the same course can never share a position on the path.
    __table_args__ = (UniqueConstraint("course_id", "order_index", name="uq_unit_order"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), index=True, nullable=False
    )
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    color_hex: Mapped[str] = mapped_column(String(7), nullable=False)

    course: Mapped["Course"] = relationship(back_populates="units")
    skills: Mapped[list["Skill"]] = relationship(
        back_populates="unit",
        cascade="all, delete-orphan",
        order_by="Skill.order_index",
    )


class Skill(Base):
    """One circular node on the winding path."""

    __tablename__ = "skills"
    __table_args__ = (UniqueConstraint("unit_id", "order_index", name="uq_skill_order"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    unit_id: Mapped[int] = mapped_column(
        ForeignKey("units.id", ondelete="CASCADE"), index=True, nullable=False
    )
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    # Icon name resolved to an SVG by the frontend, so no binary assets in the DB.
    icon: Mapped[str] = mapped_column(String(50), nullable=False)
    # How many crowns the *previous* skill needs before this one opens. Storing
    # it per-skill lets content authors gate a hard skill harder than an easy one.
    required_crowns_to_unlock: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    unit: Mapped["Unit"] = relationship(back_populates="skills")
    lessons: Mapped[list["Lesson"]] = relationship(
        back_populates="skill",
        cascade="all, delete-orphan",
        order_by="Lesson.order_index",
    )
    user_progress: Mapped[list["UserProgress"]] = relationship(
        back_populates="skill", cascade="all, delete-orphan"
    )
