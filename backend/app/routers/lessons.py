"""Lesson playing endpoints: fetch, start, answer, complete."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.lesson import (
    AnswerRead,
    CompletionRead,
    ExerciseRead,
    LessonRead,
    StartAttemptRead,
    StartAttemptRequest,
    SubmitAnswerRequest,
)
from app.services import lesson_service

router = APIRouter(tags=["lessons"])


@router.get("/lessons/{lesson_id}", response_model=LessonRead)
def read_lesson(lesson_id: int, db: Session = Depends(get_db)) -> LessonRead:
    """Return a lesson's exercises with the answer key withheld.

    ``ExerciseRead`` has no ``correct_answer`` field, so the omission is
    structural rather than something this handler has to remember to do.
    """
    lesson = lesson_service.get_lesson(db, lesson_id)
    return LessonRead(
        id=lesson.id,
        skill_id=lesson.skill_id,
        order_index=lesson.order_index,
        xp_reward=lesson.xp_reward,
        skill_title=lesson.skill.title,
        exercises=[ExerciseRead.model_validate(exercise) for exercise in lesson.exercises],
    )


@router.post("/lessons/{lesson_id}/start", response_model=StartAttemptRead, status_code=201)
def start_lesson(
    lesson_id: int, body: StartAttemptRequest, db: Session = Depends(get_db)
) -> StartAttemptRead:
    """Open an attempt and hand back its id plus the current heart count."""
    attempt, hearts = lesson_service.start_attempt(db, body.user_id, lesson_id)
    return StartAttemptRead(
        attempt_id=attempt.id, lesson_id=attempt.lesson_id, hearts_remaining=hearts
    )


@router.post("/attempts/{attempt_id}/answer", response_model=AnswerRead)
def submit_answer(
    attempt_id: int, body: SubmitAnswerRequest, db: Session = Depends(get_db)
) -> AnswerRead:
    """Grade one answer on the server and report the verdict."""
    result = lesson_service.submit_answer(db, attempt_id, body.exercise_id, body.answer)
    return AnswerRead(
        is_correct=result.is_correct,
        correct_answer=result.correct_answer,
        explanation=result.explanation,
        hearts_remaining=result.hearts_remaining,
        attempt_failed=result.attempt_failed,
    )


@router.post("/attempts/{attempt_id}/complete", response_model=CompletionRead)
def complete_attempt(attempt_id: int, db: Session = Depends(get_db)) -> CompletionRead:
    """Close the attempt, award everything it earned and return the summary."""
    summary = lesson_service.complete_attempt(db, attempt_id)
    return CompletionRead(
        **{
            key: value
            for key, value in vars(summary).items()
            if key != "unlocked_achievements"
        },
        unlocked_achievements=summary.unlocked_achievements,
    )
