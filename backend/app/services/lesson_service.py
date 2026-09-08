"""The lesson attempt lifecycle: start, answer, complete.

This is the only module that mutates a learner's progress. Routers call it and
serialise what comes back; it in turn leans on ``answer_grader`` for verdicts,
``gamification_service`` for hearts/XP/streak and ``path_service`` for unlocks.

The attempt row is what makes the flow tamper-proof: the client is handed an
``attempt_id`` and nothing else, so hearts spent and XP earned are decided here
against state the browser cannot reach.
"""

from dataclasses import dataclass, field
from datetime import date

from sqlalchemy import select, update
from sqlalchemy.orm import Session, selectinload

from app.core import clock
from app.core.config import settings
from app.models.achievement import Achievement
from app.models.course import Course, Skill, Unit
from app.models.enums import ExerciseType
from app.models.lesson import Exercise, Lesson
from app.models.progress import LessonAttempt, UserProgress
from app.models.stats import UserStats
from app.models.user import User
from app.services import answer_grader, gamification_service, path_service
from app.services.achievement_service import sync_achievements
from app.services.exceptions import (
    ConflictError,
    NotFoundError,
    OutOfHeartsError,
    SkillLockedError,
)


@dataclass(frozen=True)
class AnswerResult:
    """The verdict for one submitted answer."""

    is_correct: bool
    correct_answer: str
    explanation: str | None
    hearts_remaining: int
    attempt_failed: bool


@dataclass(frozen=True)
class CompletionSummary:
    """Everything the completion screen renders."""

    attempt_id: int
    xp_earned: int
    total_xp: int
    accuracy_percent: int
    duration_seconds: int
    is_perfect: bool
    crown_earned: bool
    skill_crowns: int
    skill_completed: bool
    current_streak: int
    streak_extended: bool
    daily_goal_xp: int
    daily_xp_earned: int
    hearts_remaining: int
    gems: int
    unlocked_achievements: list[Achievement] = field(default_factory=list)


def _require(instance: object | None, label: str) -> object:
    """Raise a 404-mapped error instead of letting ``None`` propagate."""
    if instance is None:
        raise NotFoundError("{} not found".format(label))
    return instance


def get_lesson(db: Session, lesson_id: int) -> Lesson:
    """Load a lesson with its exercises in presentation order."""
    lesson = db.scalar(
        select(Lesson).where(Lesson.id == lesson_id).options(selectinload(Lesson.exercises))
    )
    return _require(lesson, "Lesson")  # type: ignore[return-value]


def get_stats(db: Session, user_id: int) -> UserStats:
    """Load a learner's stats with heart regeneration already applied."""
    stats = db.get(UserStats, user_id)
    _require(stats, "User")
    moment = clock.now_for(stats.clock_offset_seconds)  # type: ignore[union-attr]
    return gamification_service.apply_heart_regen(stats, moment)  # type: ignore[arg-type]


def _course_for_lesson(db: Session, lesson: Lesson) -> Course:
    """Walk lesson -> skill -> unit -> course for the unlock check."""
    course = db.scalar(
        select(Course)
        .join(Unit, Unit.course_id == Course.id)
        .join(Skill, Skill.unit_id == Unit.id)
        .where(Skill.id == lesson.skill_id)
    )
    return _require(course, "Course")  # type: ignore[return-value]


def start_attempt(db: Session, user_id: int, lesson_id: int) -> tuple[LessonAttempt, int]:
    """Open an attempt, refusing if the skill is locked or hearts are empty.

    Both guards live here rather than in the router because they are rules, not
    transport concerns -- and because the same guards must hold no matter which
    entry point starts a lesson.
    """
    _require(db.get(User, user_id), "User")
    lesson = get_lesson(db, lesson_id)
    stats = get_stats(db, user_id)

    if stats.hearts <= 0:
        raise OutOfHeartsError("No hearts left. Wait for a refill or spend gems.")

    course = _course_for_lesson(db, lesson)
    path_service.sync_unlock_flags(db, course, user_id)
    progress = db.scalar(
        select(UserProgress).where(
            UserProgress.user_id == user_id, UserProgress.skill_id == lesson.skill_id
        )
    )
    if progress is None or not progress.is_unlocked:
        raise SkillLockedError("Finish the previous skill to unlock this lesson.")

    attempt = LessonAttempt(
        user_id=user_id, lesson_id=lesson_id, started_at=clock.now_for(stats.clock_offset_seconds)
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return attempt, stats.hearts


def _claim_attempt(db: Session, attempt_id: int) -> LessonAttempt:
    """Take exclusive ownership of an attempt so it can only be completed once.

    A read-then-write guard (``if attempt.is_completed: raise``) is a race: two
    concurrent requests both read False, both pass, and both return a summary
    claiming the same award. This flips the flag with a conditional UPDATE
    instead, so the database decides the winner -- whoever matches
    ``is_completed = false`` first gets rowcount 1, and every other caller gets
    0 and the same 409 a sequential retry would get.

    Portable on purpose: SQLite serialises the writers, and Postgres blocks the
    second UPDATE on the row lock until the first commits, after which the
    predicate no longer matches. Neither needs an explicit lock statement.
    """
    attempt = db.get(LessonAttempt, attempt_id)
    _require(attempt, "Attempt")

    claimed = db.execute(
        update(LessonAttempt)
        .where(LessonAttempt.id == attempt_id, LessonAttempt.is_completed.is_(False))
        .values(is_completed=True)
    ).rowcount
    if not claimed:
        raise ConflictError("This attempt is already complete.")
    return attempt  # type: ignore[return-value]


def _load_open_attempt(db: Session, attempt_id: int) -> LessonAttempt:
    """Fetch an attempt and refuse to touch one that is already finished."""
    attempt = db.get(LessonAttempt, attempt_id)
    _require(attempt, "Attempt")
    if attempt.is_completed:  # type: ignore[union-attr]
        raise ConflictError("This attempt is already complete.")
    return attempt  # type: ignore[return-value]


def submit_answer(
    db: Session, attempt_id: int, exercise_id: int, answer: dict
) -> AnswerResult:
    """Grade one answer and charge a heart if it is wrong.

    The answer key is read here and compared here; only the verdict and the
    single revealed answer travel back to the client.
    """
    attempt = _load_open_attempt(db, attempt_id)
    exercise = db.get(Exercise, exercise_id)
    _require(exercise, "Exercise")
    if exercise.lesson_id != attempt.lesson_id:  # type: ignore[union-attr]
        raise ConflictError("That exercise does not belong to this lesson.")

    stats = get_stats(db, attempt.user_id)
    is_correct = answer_grader.grade(
        exercise.type, exercise.correct_answer, answer  # type: ignore[union-attr]
    )

    attempt.exercises_answered += 1
    if not is_correct:
        # Counted on the attempt even when the learner is already at zero, so
        # the accuracy shown on the completion screen stays exact.
        attempt.hearts_lost += 1
        gamification_service.lose_heart(stats, clock.now_for(stats.clock_offset_seconds))

    db.commit()
    return AnswerResult(
        is_correct=is_correct,
        correct_answer=answer_grader.format_correct_answer(
            exercise.type, exercise.correct_answer  # type: ignore[union-attr]
        ),
        explanation=exercise.explanation,  # type: ignore[union-attr]
        hearts_remaining=stats.hearts,
        attempt_failed=stats.hearts <= 0,
    )


def check_pair(db: Session, attempt_id: int, exercise_id: int, left: str, right: str) -> bool:
    """Verify one tile pairing without revealing the rest of the board.

    Match-pairs is the one exercise whose interaction *requires* feedback mid-
    answer: a board that only tells you at the end which of five links was wrong
    is unplayable. Rather than shipping the mapping to the client, the client
    asks about one link at a time -- exactly the single bit the game would show
    anyway -- and the answer key stays here.

    A mis-tap costs no heart. The heart cost for this exercise is applied by the
    normal grading path when the finished board is submitted, and since a board
    can only be finished by matching every pair, a learner who perseveres keeps
    their hearts. That mirrors how the real game treats this exercise type.
    """
    attempt = _load_open_attempt(db, attempt_id)
    exercise = db.get(Exercise, exercise_id)
    _require(exercise, "Exercise")
    if exercise.lesson_id != attempt.lesson_id:  # type: ignore[union-attr]
        raise ConflictError("That exercise does not belong to this lesson.")
    if exercise.type is not ExerciseType.MATCH_PAIRS:  # type: ignore[union-attr]
        raise ConflictError("Only match-pairs exercises can be checked one pair at a time.")

    return _single_pair_matches(exercise.correct_answer, left, right)  # type: ignore[union-attr]


def _single_pair_matches(correct_answer: dict, left: str, right: str) -> bool:
    """True when this one link appears in the stored mapping."""
    pairs = correct_answer.get("pairs")
    if not isinstance(pairs, dict):
        return False
    normalized = {
        answer_grader.normalize(str(key)): answer_grader.normalize(str(value))
        for key, value in pairs.items()
    }
    return normalized.get(answer_grader.normalize(left)) == answer_grader.normalize(right)


def _award_crown(
    db: Session, user_id: int, lesson: Lesson, current_attempt_id: int
) -> tuple[bool, UserProgress]:
    """Grant a crown for the first completion of this specific lesson.

    Replaying a lesson is allowed and still pays XP, but crowns count *distinct*
    lessons finished, so a learner cannot farm a skill to gold by repeating its
    easiest lesson.

    ``current_attempt_id`` is excluded from the lookback: the caller has already
    claimed this attempt as complete, so without the exclusion every first
    completion would find *itself* and quietly withhold the crown.
    """
    previously_done = db.scalar(
        select(LessonAttempt.id).where(
            LessonAttempt.user_id == user_id,
            LessonAttempt.lesson_id == lesson.id,
            LessonAttempt.is_completed.is_(True),
            LessonAttempt.id != current_attempt_id,
        )
    )
    progress = db.scalar(
        select(UserProgress).where(
            UserProgress.user_id == user_id, UserProgress.skill_id == lesson.skill_id
        )
    )
    if progress is None:
        # Explicit zeros: column defaults are applied at flush, so without
        # them the increment below would run against None.
        progress = UserProgress(
            user_id=user_id,
            skill_id=lesson.skill_id,
            crowns=0,
            lessons_completed=0,
            is_unlocked=True,
        )
        db.add(progress)
    if previously_done is not None:
        return False, progress
    progress.crowns += 1
    progress.lessons_completed += 1
    return True, progress


def complete_attempt(db: Session, attempt_id: int) -> CompletionSummary:
    """Close an attempt: award XP, crowns, streak and any achievements.

    Ordered deliberately -- XP is banked before the streak is recomputed, and
    unlock flags are refreshed before achievements are synced, so every derived
    value in the returned summary reflects the same post-lesson world.
    """
    attempt = _claim_attempt(db, attempt_id)
    lesson = get_lesson(db, attempt.lesson_id)
    stats = get_stats(db, attempt.user_id)
    today: date = clock.today_for(stats.clock_offset_seconds)

    streak_before = stats.current_streak
    xp = gamification_service.calculate_lesson_xp(
        lesson.xp_reward, attempt.hearts_lost, stats.hearts
    )

    crown_earned, progress = _award_crown(db, attempt.user_id, lesson, attempt.id)

    attempt.is_completed = True
    attempt.completed_at = clock.now_for(stats.clock_offset_seconds)
    attempt.xp_earned = xp

    stats.total_xp += xp
    gamification_service.record_daily_xp(db, attempt.user_id, xp, today)
    db.flush()  # Make the ledger row visible to the streak query below.
    gamification_service.refresh_streak(db, stats, today)

    course = _course_for_lesson(db, lesson)
    path_service.sync_unlock_flags(db, course, attempt.user_id)
    unlocked = sync_achievements(db, attempt.user_id)

    lesson_count = len(db.scalars(select(Lesson.id).where(Lesson.skill_id == lesson.skill_id)).all())
    answered = attempt.exercises_answered or len(lesson.exercises)
    accuracy = round(100 * max(0, answered - attempt.hearts_lost) / answered) if answered else 100
    duration = int((attempt.completed_at - attempt.started_at).total_seconds())

    db.commit()

    return CompletionSummary(
        attempt_id=attempt.id,
        xp_earned=xp,
        total_xp=stats.total_xp,
        accuracy_percent=accuracy,
        duration_seconds=max(0, duration),
        is_perfect=attempt.hearts_lost == 0,
        crown_earned=crown_earned,
        skill_crowns=progress.crowns,
        skill_completed=progress.crowns >= lesson_count > 0,
        current_streak=stats.current_streak,
        streak_extended=stats.current_streak > streak_before,
        daily_goal_xp=stats.daily_goal_xp,
        daily_xp_earned=gamification_service.xp_earned_on(db, attempt.user_id, today),
        hearts_remaining=stats.hearts,
        gems=stats.gems,
        unlocked_achievements=unlocked,
    )


def refill_hearts_with_gems(db: Session, user_id: int) -> UserStats:
    """Spend gems for a full heart bar, or refuse with a 400-mapped error."""
    stats = get_stats(db, user_id)
    if not gamification_service.refill_hearts(stats, clock.now_for(stats.clock_offset_seconds)):
        raise ConflictError(
            "Hearts are already full or you need {} gems.".format(settings.heart_refill_gem_cost)
        )
    db.commit()
    return stats
