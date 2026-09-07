"""Skill unlocking and the derived path states."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.course import Course, Skill, Unit
from app.models.enums import SkillState
from app.models.lesson import Lesson
from app.models.progress import UserProgress
from app.models.user import User
from app.services import path_service
from app.services.path_service import derive_state
from tests.test_xp import play


class TestDeriveState:
    """The pure mapping from (crowns, lessons, unlocked) onto a path state."""

    def test_locked_when_not_unlocked_and_untouched(self) -> None:
        assert derive_state(0, 3, is_unlocked=False) is SkillState.LOCKED

    def test_available_when_unlocked_but_unstarted(self) -> None:
        assert derive_state(0, 3, is_unlocked=True) is SkillState.AVAILABLE

    def test_in_progress_with_some_crowns(self) -> None:
        assert derive_state(1, 3, is_unlocked=True) is SkillState.IN_PROGRESS

    def test_completed_when_every_lesson_has_a_crown(self) -> None:
        assert derive_state(3, 3, is_unlocked=True) is SkillState.COMPLETED

    def test_crowns_beyond_the_lesson_count_still_read_as_completed(self) -> None:
        assert derive_state(5, 3, is_unlocked=True) is SkillState.COMPLETED

    def test_a_skill_with_no_lessons_is_never_complete(self) -> None:
        assert derive_state(0, 0, is_unlocked=True) is SkillState.AVAILABLE


def flat_skills(db: Session, course: Course) -> list[Skill]:
    """Every skill in path order: units by index, then skills within each unit."""
    units = db.scalars(
        select(Unit).where(Unit.course_id == course.id).order_by(Unit.order_index)
    ).all()
    return [
        skill
        for unit in units
        for skill in sorted(unit.skills, key=lambda item: item.order_index)
    ]


def states(db: Session, course: Course, user: User) -> list[SkillState]:
    """The state of every skill on the path, in order."""
    return [
        node.state
        for unit_node in path_service.build_path(db, course, user.id)
        for node in unit_node.skills
    ]


class TestPathUnlocking:
    def test_only_the_first_skill_is_open_for_a_new_learner(
        self, db: Session, course: Course, user: User
    ) -> None:
        result = states(db, course, user)
        assert result[0] is SkillState.AVAILABLE
        assert set(result[1:]) == {SkillState.LOCKED}

    def test_one_crown_unlocks_the_next_skill(
        self, db: Session, course: Course, user: User
    ) -> None:
        skills = flat_skills(db, course)
        play(db, user, skills[0].lessons[0])
        result = states(db, course, user)
        assert result[0] is SkillState.IN_PROGRESS
        assert result[1] is SkillState.AVAILABLE
        assert result[2] is SkillState.LOCKED

    def test_unlocking_respects_the_required_crown_count(
        self, db: Session, course: Course, user: User
    ) -> None:
        skills = flat_skills(db, course)
        skills[0].required_crowns_to_unlock = 2
        db.commit()

        play(db, user, skills[0].lessons[0])
        assert states(db, course, user)[1] is SkillState.LOCKED

        play(db, user, skills[0].lessons[1])
        assert states(db, course, user)[1] is SkillState.AVAILABLE

    def test_finishing_a_skill_marks_it_completed(
        self, db: Session, course: Course, user: User
    ) -> None:
        skill = flat_skills(db, course)[0]
        for lesson in skill.lessons:
            play(db, user, lesson)
        assert states(db, course, user)[0] is SkillState.COMPLETED

    def test_the_path_stays_linear_across_a_unit_boundary(
        self, db: Session, course: Course, user: User
    ) -> None:
        """The first skill of Unit 2 opens only after the last skill of Unit 1."""
        units = path_service.build_path(db, course, user.id)
        unit_one_size = len(units[0].skills)
        skills = flat_skills(db, course)

        for skill in skills[: unit_one_size - 1]:
            for lesson in skill.lessons:
                play(db, user, lesson)
        assert states(db, course, user)[unit_one_size] is SkillState.LOCKED

        play(db, user, skills[unit_one_size - 1].lessons[0])
        assert states(db, course, user)[unit_one_size] is SkillState.AVAILABLE

    def test_crowns_and_lesson_counts_are_reported_per_node(
        self, db: Session, course: Course, user: User
    ) -> None:
        skill = flat_skills(db, course)[0]
        play(db, user, skill.lessons[0])
        node = path_service.build_path(db, course, user.id)[0].skills[0]
        assert node.crowns == 1
        assert node.lesson_count == len(skill.lessons)

    def test_a_started_skill_stays_unlocked_even_if_the_rule_changes(
        self, db: Session, course: Course, user: User
    ) -> None:
        """Crowns already earned can never be taken away by a content edit."""
        skills = flat_skills(db, course)
        play(db, user, skills[0].lessons[0])
        play(db, user, skills[1].lessons[0])
        skills[0].required_crowns_to_unlock = 99
        db.commit()
        assert states(db, course, user)[1] is SkillState.IN_PROGRESS


class TestUnlockFlagPersistence:
    def test_sync_writes_the_flag_onto_user_progress(
        self, db: Session, course: Course, user: User
    ) -> None:
        path_service.sync_unlock_flags(db, course, user.id)
        db.commit()
        rows = db.scalars(select(UserProgress).where(UserProgress.user_id == user.id)).all()
        # Only the open skill gets a row; locked skills stay absent until reached.
        assert len(rows) == 1
        assert rows[0].is_unlocked is True

    def test_sync_is_idempotent(self, db: Session, course: Course, user: User) -> None:
        for _ in range(3):
            path_service.sync_unlock_flags(db, course, user.id)
        db.commit()
        rows = db.scalars(select(UserProgress).where(UserProgress.user_id == user.id)).all()
        assert len(rows) == 1

    def test_lesson_count_query_covers_every_skill_with_lessons(
        self, db: Session, course: Course, user: User
    ) -> None:
        total = len(db.scalars(select(Lesson.id)).all())
        counted = sum(
            node.lesson_count
            for unit_node in path_service.build_path(db, course, user.id)
            for node in unit_node.skills
        )
        assert counted == total
