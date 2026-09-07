"""Achievement progress and unlocking.

Achievements are data: each row names the learner metric it tracks and the
target value. This module computes every metric once, then walks the definitions
generically -- adding a badge is an INSERT, never a code change.
"""

from dataclasses import asdict, dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core import clock
from app.models.achievement import Achievement, UserAchievement
from app.models.progress import LessonAttempt, UserProgress
from app.models.stats import UserStats


@dataclass(frozen=True)
class LearnerMetrics:
    """Every value an achievement can be measured against.

    Computed in one pass so syncing six badges costs four queries, not six.
    """

    lessons_completed: int
    perfect_lessons: int
    total_crowns: int
    total_xp: int
    longest_streak: int


def collect_metrics(db: Session, user_id: int) -> LearnerMetrics:
    """Aggregate the learner's current standing across every tracked metric."""
    completed = db.scalar(
        select(func.count(LessonAttempt.id)).where(
            LessonAttempt.user_id == user_id, LessonAttempt.is_completed.is_(True)
        )
    )
    perfect = db.scalar(
        select(func.count(LessonAttempt.id)).where(
            LessonAttempt.user_id == user_id,
            LessonAttempt.is_completed.is_(True),
            LessonAttempt.hearts_lost == 0,
        )
    )
    crowns = db.scalar(
        select(func.coalesce(func.sum(UserProgress.crowns), 0)).where(
            UserProgress.user_id == user_id
        )
    )
    stats = db.get(UserStats, user_id)
    return LearnerMetrics(
        lessons_completed=completed or 0,
        perfect_lessons=perfect or 0,
        total_crowns=crowns or 0,
        total_xp=stats.total_xp if stats else 0,
        longest_streak=stats.longest_streak if stats else 0,
    )


def sync_achievements(db: Session, user_id: int) -> list[Achievement]:
    """Recompute every badge's progress and return the ones newly unlocked.

    Idempotent: re-running it never re-unlocks a badge, because ``unlocked_at``
    is only written when it is currently NULL. The caller uses the returned list
    to raise a toast, so a replayed request cannot spam the learner.
    """
    metrics = asdict(collect_metrics(db, user_id))
    existing = {
        row.achievement_id: row
        for row in db.scalars(
            select(UserAchievement).where(UserAchievement.user_id == user_id)
        ).all()
    }

    newly_unlocked: list[Achievement] = []
    for achievement in db.scalars(select(Achievement).order_by(Achievement.id)).all():
        value = metrics.get(achievement.metric, 0)
        row = existing.get(achievement.id)
        if row is None:
            row = UserAchievement(user_id=user_id, achievement_id=achievement.id, progress=0)
            db.add(row)
        # Progress is clamped so the UI can render progress/target directly.
        row.progress = min(value, achievement.target)
        if row.unlocked_at is None and value >= achievement.target:
            row.unlocked_at = clock.now()
            newly_unlocked.append(achievement)

    return newly_unlocked
