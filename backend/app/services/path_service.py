"""Builds the learning path: which skills are locked, available or done.

Skill state is *derived*, never stored. A stored state would be a second source
of truth that can drift from the crowns that produced it; deriving it means the
path is always consistent with progress, and the unlock rule can be changed
without a data migration.
"""

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.course import Course, Skill, Unit
from app.models.enums import SkillState
from app.models.lesson import Lesson
from app.models.progress import UserProgress


@dataclass(frozen=True)
class SkillNode:
    """One node on the path, with everything the frontend needs to draw it."""

    skill: Skill
    lesson_count: int
    crowns: int
    state: SkillState


@dataclass(frozen=True)
class UnitNode:
    """A unit header plus its ordered skill nodes."""

    unit: Unit
    skills: list[SkillNode]


def _lesson_counts(db: Session, course_id: int) -> dict[int, int]:
    """How many lessons each skill in the course has, in one query."""
    rows = db.execute(
        select(Lesson.skill_id, func.count(Lesson.id))
        .join(Skill, Skill.id == Lesson.skill_id)
        .join(Unit, Unit.id == Skill.unit_id)
        .where(Unit.course_id == course_id)
        .group_by(Lesson.skill_id)
    ).all()
    return {skill_id: count for skill_id, count in rows}


def _crowns_by_skill(db: Session, user_id: int) -> dict[int, int]:
    """The learner's crown count per skill, in one query."""
    rows = db.execute(
        select(UserProgress.skill_id, UserProgress.crowns).where(UserProgress.user_id == user_id)
    ).all()
    return {skill_id: crowns for skill_id, crowns in rows}


def derive_state(crowns: int, lesson_count: int, is_unlocked: bool) -> SkillState:
    """Map (crowns, lessons, unlocked) onto the four path states.

    A skill is complete when it has a crown for every lesson; started but not
    finished is in-progress; unlocked with no crowns is available.
    """
    if crowns >= lesson_count > 0:
        return SkillState.COMPLETED
    if crowns > 0:
        return SkillState.IN_PROGRESS
    return SkillState.AVAILABLE if is_unlocked else SkillState.LOCKED


def build_path(db: Session, course: Course, user_id: int) -> list[UnitNode]:
    """Assemble the full path for one learner.

    Unlocking walks the course in path order -- units by ``order_index``, then
    skills within each unit. The very first skill is always open; every other
    skill opens once the skill before it on the path has earned its
    ``required_crowns_to_unlock``. At a unit boundary "the skill before it" is
    the last skill of the previous unit, which keeps the trail strictly linear
    the way the UI draws it.
    """
    units = db.scalars(
        select(Unit)
        .where(Unit.course_id == course.id)
        .order_by(Unit.order_index)
        .options(selectinload(Unit.skills))
    ).all()

    lesson_counts = _lesson_counts(db, course.id)
    crowns_by_skill = _crowns_by_skill(db, user_id)

    result: list[UnitNode] = []
    previous_unlocks_next = True  # The first skill on the path is always open.

    for unit in units:
        nodes: list[SkillNode] = []
        for skill in sorted(unit.skills, key=lambda item: item.order_index):
            crowns = crowns_by_skill.get(skill.id, 0)
            lesson_count = lesson_counts.get(skill.id, 0)
            is_unlocked = previous_unlocks_next or crowns > 0
            nodes.append(
                SkillNode(
                    skill=skill,
                    lesson_count=lesson_count,
                    crowns=crowns,
                    state=derive_state(crowns, lesson_count, is_unlocked),
                )
            )
            previous_unlocks_next = crowns >= skill.required_crowns_to_unlock
        result.append(UnitNode(unit=unit, skills=nodes))

    return result


def sync_unlock_flags(db: Session, course: Course, user_id: int) -> None:
    """Persist the derived unlock flag onto ``user_progress``.

    The flag is a denormalised convenience for the lesson-start guard, which
    must answer "may this learner open this skill?" without rebuilding the whole
    path. ``build_path`` remains the authority; this only writes down its answer.
    """
    # Every existing row is loaded once rather than queried per skill: twelve
    # skills would otherwise mean twelve round trips on every lesson start.
    rows = {
        row.skill_id: row
        for row in db.scalars(
            select(UserProgress).where(UserProgress.user_id == user_id)
        ).all()
    }
    for unit_node in build_path(db, course, user_id):
        for node in unit_node.skills:
            unlocked = node.state is not SkillState.LOCKED
            row = rows.get(node.skill.id)
            if row is None:
                if not unlocked:
                    continue
                row = UserProgress(
                    user_id=user_id, skill_id=node.skill.id, crowns=0, lessons_completed=0
                )
                db.add(row)
                rows[node.skill.id] = row
            row.is_unlocked = unlocked
    # Flushed so callers that immediately re-query see these rows; the session
    # runs with autoflush off, so a pending row would otherwise be invisible.
    db.flush()
