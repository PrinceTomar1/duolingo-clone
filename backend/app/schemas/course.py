"""Response models for the learning path."""

from pydantic import BaseModel, Field

from app.models.enums import SkillState
from app.schemas.common import ORMModel


class SkillRead(ORMModel):
    """One node on the path, with its state already computed server-side."""

    id: int
    order_index: int
    title: str
    icon: str
    lesson_count: int
    crowns: int
    state: SkillState
    required_crowns_to_unlock: int


class UnitRead(ORMModel):
    """A unit header and its ordered skills."""

    id: int
    order_index: int
    title: str
    description: str
    color_hex: str
    skills: list[SkillRead]


class CoursePathRead(BaseModel):
    """The whole path for one learner: everything the Learn screen renders."""

    course_id: int
    title: str
    from_language: str
    to_language: str
    units: list[UnitRead]
    total_crowns: int = Field(description="Crowns earned across the entire course")


class CourseSummaryRead(ORMModel):
    """One row of the language picker -- enough to list and select a course."""

    id: int
    title: str
    from_language: str
    to_language: str
