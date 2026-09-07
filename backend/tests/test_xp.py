"""The XP formula and the end-to-end lesson attempt flow."""

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import clock
from app.core.config import settings
from app.models.course import Course, Skill, Unit
from app.models.lesson import Lesson
from app.models.stats import UserStats
from app.models.user import User
from app.services import gamification_service as gamification
from app.services import lesson_service
from app.services.exceptions import ConflictError, OutOfHeartsError


class TestXpFormula:
    """10 base, +5 for a flawless run, +2 per surviving heart."""

    def test_perfect_lesson_with_a_full_bar(self) -> None:
        assert gamification.calculate_lesson_xp(10, hearts_lost=0, hearts_remaining=5) == 25

    def test_one_mistake_loses_the_perfect_bonus(self) -> None:
        assert gamification.calculate_lesson_xp(10, hearts_lost=1, hearts_remaining=4) == 18

    def test_scraping_through_with_no_hearts(self) -> None:
        assert gamification.calculate_lesson_xp(10, hearts_lost=5, hearts_remaining=0) == 10

    def test_lesson_can_override_the_base_award(self) -> None:
        assert gamification.calculate_lesson_xp(30, hearts_lost=0, hearts_remaining=5) == 45

    @pytest.mark.parametrize("remaining", [-3, -1])
    def test_negative_hearts_never_subtract_xp(self, remaining: int) -> None:
        assert gamification.calculate_lesson_xp(10, hearts_lost=1, hearts_remaining=remaining) == 10

    def test_formula_matches_the_configured_constants(self) -> None:
        expected = (
            settings.base_lesson_xp
            + settings.perfect_lesson_bonus_xp
            + 3 * settings.xp_per_remaining_heart
        )
        assert gamification.calculate_lesson_xp(settings.base_lesson_xp, 0, 3) == expected


def first_lesson(db: Session, course: Course) -> Lesson:
    """The very first lesson on the path, which is always unlocked."""
    unit = db.scalars(
        select(Unit).where(Unit.course_id == course.id).order_by(Unit.order_index)
    ).first()
    skill = db.scalars(
        select(Skill).where(Skill.unit_id == unit.id).order_by(Skill.order_index)
    ).first()
    return db.scalars(
        select(Lesson).where(Lesson.skill_id == skill.id).order_by(Lesson.order_index)
    ).first()


def play(db: Session, user: User, lesson: Lesson, wrong: int = 0) -> lesson_service.CompletionSummary:
    """Run a whole lesson, deliberately failing the first ``wrong`` exercises."""
    attempt, _ = lesson_service.start_attempt(db, user.id, lesson.id)
    for index, exercise in enumerate(lesson.exercises):
        if index < wrong:
            answer = {"choice": "definitely-not-the-answer", "text": "", "words": [], "pairs": []}
        elif exercise.correct_answer.get("choice") is not None:
            answer = {"choice": exercise.correct_answer["choice"]}
        elif exercise.correct_answer.get("words") is not None:
            answer = {"words": exercise.correct_answer["words"]}
        elif exercise.correct_answer.get("accepted") is not None:
            answer = {"text": exercise.correct_answer["accepted"][0]}
        else:
            answer = {
                "pairs": [
                    {"left": left, "right": right}
                    for left, right in exercise.correct_answer["pairs"].items()
                ]
            }
        lesson_service.submit_answer(db, attempt.id, exercise.id, answer)
    return lesson_service.complete_attempt(db, attempt.id)


class TestLessonCompletion:
    def test_perfect_run_awards_the_full_bonus(
        self, db: Session, course: Course, user: User
    ) -> None:
        summary = play(db, user, first_lesson(db, course))
        assert summary.is_perfect is True
        assert summary.xp_earned == 25
        assert summary.total_xp == 25
        assert summary.accuracy_percent == 100
        assert summary.hearts_remaining == 5

    def test_mistakes_cost_hearts_xp_and_accuracy(
        self, db: Session, course: Course, user: User
    ) -> None:
        lesson = first_lesson(db, course)
        summary = play(db, user, lesson, wrong=2)
        assert summary.is_perfect is False
        assert summary.hearts_remaining == 3
        assert summary.xp_earned == gamification.calculate_lesson_xp(10, 2, 3)
        # Seven of nine exercises answered correctly.
        assert summary.accuracy_percent == round(100 * 7 / 9)

    def test_completion_banks_xp_in_the_daily_ledger_and_starts_a_streak(
        self, db: Session, course: Course, user: User
    ) -> None:
        summary = play(db, user, first_lesson(db, course))
        assert summary.current_streak == 1
        assert summary.streak_extended is True
        assert summary.daily_xp_earned == summary.xp_earned
        assert gamification.xp_earned_on(db, user.id, clock.today()) == summary.xp_earned

    def test_first_completion_earns_a_crown(
        self, db: Session, course: Course, user: User
    ) -> None:
        summary = play(db, user, first_lesson(db, course))
        assert summary.crown_earned is True
        assert summary.skill_crowns == 1

    def test_replaying_a_lesson_pays_xp_but_not_a_second_crown(
        self, db: Session, course: Course, user: User
    ) -> None:
        lesson = first_lesson(db, course)
        play(db, user, lesson)
        replay = play(db, user, lesson)
        assert replay.crown_earned is False
        assert replay.skill_crowns == 1
        assert replay.xp_earned > 0
        assert replay.total_xp == 50

    def test_second_lesson_the_same_day_does_not_extend_the_streak(
        self, db: Session, course: Course, user: User
    ) -> None:
        lesson = first_lesson(db, course)
        play(db, user, lesson)
        second = play(db, user, lesson)
        assert second.current_streak == 1
        assert second.streak_extended is False

    def test_finishing_every_lesson_completes_the_skill(
        self, db: Session, course: Course, user: User
    ) -> None:
        lesson = first_lesson(db, course)
        lessons = db.scalars(
            select(Lesson).where(Lesson.skill_id == lesson.skill_id).order_by(Lesson.order_index)
        ).all()
        for item in lessons:
            summary = play(db, user, item)
        assert summary.skill_completed is True
        assert summary.skill_crowns == len(lessons)

    def test_completing_an_attempt_twice_is_rejected(
        self, db: Session, course: Course, user: User
    ) -> None:
        lesson = first_lesson(db, course)
        attempt, _ = lesson_service.start_attempt(db, user.id, lesson.id)
        lesson_service.complete_attempt(db, attempt.id)
        with pytest.raises(ConflictError):
            lesson_service.complete_attempt(db, attempt.id)

    def test_answering_an_exercise_from_another_lesson_is_rejected(
        self, db: Session, course: Course, user: User
    ) -> None:
        lesson = first_lesson(db, course)
        other = db.scalars(
            select(Lesson).where(Lesson.id != lesson.id).order_by(Lesson.id)
        ).first()
        attempt, _ = lesson_service.start_attempt(db, user.id, lesson.id)
        with pytest.raises(ConflictError):
            lesson_service.submit_answer(
                db, attempt.id, other.exercises[0].id, {"choice": "anything"}
            )


class TestHeartsGateTheLesson:
    def test_running_out_of_hearts_flags_the_attempt_as_failed(
        self, db: Session, course: Course, user: User
    ) -> None:
        lesson = first_lesson(db, course)
        attempt, _ = lesson_service.start_attempt(db, user.id, lesson.id)
        results = [
            lesson_service.submit_answer(db, attempt.id, exercise.id, {"choice": "wrong"})
            for exercise in lesson.exercises[:5]
        ]
        assert [result.hearts_remaining for result in results] == [4, 3, 2, 1, 0]
        assert results[-1].attempt_failed is True

    def test_a_learner_with_no_hearts_cannot_start_a_lesson(
        self, db: Session, course: Course, user: User
    ) -> None:
        stats = db.get(UserStats, user.id)
        stats.hearts = 0
        stats.hearts_updated_at = clock.now()
        db.commit()
        with pytest.raises(OutOfHeartsError):
            lesson_service.start_attempt(db, user.id, first_lesson(db, course).id)

    def test_gem_refill_restores_the_bar(self, db: Session, course: Course, user: User) -> None:
        stats = db.get(UserStats, user.id)
        stats.hearts = 0
        db.commit()
        refilled = lesson_service.refill_hearts_with_gems(db, user.id)
        assert refilled.hearts == settings.max_hearts
        assert refilled.gems == 500 - settings.heart_refill_gem_cost

    def test_gem_refill_refused_when_the_bar_is_full(
        self, db: Session, course: Course, user: User
    ) -> None:
        with pytest.raises(ConflictError):
            lesson_service.refill_hearts_with_gems(db, user.id)
