"""Learning-path endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.course import Course, Skill
from app.models.user import User
from app.schemas.course import CoursePathRead, CourseSummaryRead, SkillRead, UnitRead
from app.services import path_service
from app.services.exceptions import NotFoundError

router = APIRouter(prefix="/course", tags=["course"])


@router.get("/list", response_model=list[CourseSummaryRead])
def read_courses(db: Session = Depends(get_db)) -> list[Course]:
    """Every course available to learn, for the language picker."""
    return list(db.scalars(select(Course).order_by(Course.id)).all())


@router.get("/path", response_model=CoursePathRead)
def read_course_path(
    user_id: int = Query(description="Learner whose progress the path is computed for"),
    course_id: int | None = Query(
        default=None, description="Which course to show. Defaults to the first seeded course."
    ),
    db: Session = Depends(get_db),
) -> CoursePathRead:
    """Return every unit and skill with this learner's per-skill state.

    The router does no computing: it resolves the course, hands the work to
    ``path_service`` and reshapes the result into the response model.
    """
    # An unknown learner used to come back 200 with every skill locked, which
    # reads as "you have no progress" rather than "that user does not exist" --
    # and disagrees with /users/{id}/stats, which 404s. Answer the same way here.
    if db.get(User, user_id) is None:
        raise NotFoundError("User not found")

    if course_id is not None:
        course = db.get(Course, course_id)
    else:
        course = db.scalar(select(Course).order_by(Course.id))
    if course is None:
        raise NotFoundError("No course has been seeded yet.")

    units = path_service.build_path(db, course, user_id)
    return CoursePathRead(
        course_id=course.id,
        title=course.title,
        from_language=course.from_language,
        to_language=course.to_language,
        units=[
            UnitRead(
                id=unit_node.unit.id,
                order_index=unit_node.unit.order_index,
                title=unit_node.unit.title,
                description=unit_node.unit.description,
                color_hex=unit_node.unit.color_hex,
                skills=[
                    SkillRead(
                        id=node.skill.id,
                        order_index=node.skill.order_index,
                        title=node.skill.title,
                        icon=node.skill.icon,
                        lesson_count=node.lesson_count,
                        crowns=node.crowns,
                        state=node.state,
                        required_crowns_to_unlock=node.skill.required_crowns_to_unlock,
                    )
                    for node in unit_node.skills
                ],
            )
            for unit_node in units
        ],
        total_crowns=sum(node.crowns for unit_node in units for node in unit_node.skills),
    )


@router.get("/skills/{skill_id}/lessons", response_model=list[int])
def read_skill_lesson_ids(skill_id: int, db: Session = Depends(get_db)) -> list[int]:
    """Lesson ids for a skill, in order.

    The path screen needs this to send a learner into the *next* unfinished
    lesson when they tap a node, without downloading every lesson's exercises.
    """
    from app.models.lesson import Lesson

    # An empty list is a meaningful answer for a real skill that has no lessons
    # yet; for a skill id that does not exist it is a lie, so separate the two.
    if db.get(Skill, skill_id) is None:
        raise NotFoundError("Skill not found")

    return list(
        db.scalars(
            select(Lesson.id).where(Lesson.skill_id == skill_id).order_by(Lesson.order_index)
        ).all()
    )
