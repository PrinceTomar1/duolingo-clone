"""Request and response models for playing a lesson."""

from typing import Any

from pydantic import BaseModel, Field

from app.models.enums import ExerciseType
from app.schemas.common import ORMModel


class ExerciseRead(ORMModel):
    """An exercise as the client is allowed to see it.

    Note what is *absent*: ``correct_answer`` and ``explanation``. Both would
    give the answer away, so neither field exists on this model at all -- the
    leak is prevented by the schema, not by remembering to strip a key.
    """

    id: int
    order_index: int
    type: ExerciseType
    prompt: str
    payload: dict[str, Any]
    audio_url: str | None = None


class LessonRead(ORMModel):
    """A lesson and its exercises, ready to play."""

    id: int
    skill_id: int
    order_index: int
    xp_reward: int
    skill_title: str
    exercises: list[ExerciseRead]


class StartAttemptRequest(BaseModel):
    """Body for opening an attempt."""

    user_id: int


class StartAttemptRead(BaseModel):
    """The handle the client holds for the rest of the lesson."""

    attempt_id: int
    lesson_id: int
    hearts_remaining: int


class SubmitAnswerRequest(BaseModel):
    """One graded submission.

    ``answer`` is an open object because its shape depends on the exercise type
    (a chosen option, an ordered word list, a set of pairs). Validating the
    shape happens in the grader, which is the only place that knows the type.
    """

    exercise_id: int
    answer: dict[str, Any] = Field(default_factory=dict)


class AnswerRead(BaseModel):
    """The verdict for one answer, plus the single revealed correct answer."""

    is_correct: bool
    correct_answer: str
    explanation: str | None = None
    hearts_remaining: int
    attempt_failed: bool = Field(
        description="True when the last heart is gone and the lesson has failed"
    )


class UnlockedAchievementRead(ORMModel):
    """A badge that popped during this lesson, for the toast."""

    code: str
    title: str
    description: str
    icon: str
    color_hex: str


class CompletionRead(BaseModel):
    """Everything the completion screen shows."""

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
    unlocked_achievements: list[UnlockedAchievementRead] = []
