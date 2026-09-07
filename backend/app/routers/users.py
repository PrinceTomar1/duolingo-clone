"""Learner identity, stats, profile and heart refills."""

from datetime import timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core import clock
from app.core.config import settings
from app.core.database import get_db
from app.models.achievement import Achievement, UserAchievement
from app.models.progress import LessonAttempt, UserProgress
from app.models.stats import DailyXp, UserStats
from app.models.user import User
from app.schemas.user import (
    AchievementRead,
    DailyXpRead,
    UserProfileRead,
    UserRead,
    UserStatsRead,
)
from app.services import gamification_service, lesson_service
from app.services.exceptions import NotFoundError

router = APIRouter(prefix="/users", tags=["users"])


def _stats_payload(db: Session, stats: UserStats) -> UserStatsRead:
    """Assemble the stats response, including the two derived heart fields."""
    today = clock.today()
    return UserStatsRead(
        user_id=stats.user_id,
        total_xp=stats.total_xp,
        current_streak=stats.current_streak,
        longest_streak=stats.longest_streak,
        last_active_date=stats.last_active_date,
        hearts=stats.hearts,
        max_hearts=settings.max_hearts,
        seconds_until_next_heart=gamification_service.seconds_until_next_heart(stats),
        gems=stats.gems,
        daily_goal_xp=stats.daily_goal_xp,
        daily_xp_earned=gamification_service.xp_earned_on(db, stats.user_id, today),
        weekly_xp=gamification_service.xp_earned_since(
            db, stats.user_id, today - timedelta(days=6)
        ),
    )


@router.get("/by-username/{username}", response_model=UserRead)
def read_user_by_username(username: str, db: Session = Depends(get_db)) -> User:
    """Resolve a username to a learner.

    The frontend boots from this rather than a hardcoded id, so the demo learner
    keeps working whichever order the seed inserted rows in.
    """
    user = db.scalar(select(User).where(User.username == username))
    if user is None:
        raise NotFoundError("No user named '{}'.".format(username))
    return user


@router.get("/{user_id}/stats", response_model=UserStatsRead)
def read_user_stats(user_id: int, db: Session = Depends(get_db)) -> UserStatsRead:
    """Current hearts, streak, gems and today's progress toward the daily goal.

    Reading applies lazy heart regeneration first, so the number returned is
    always the number the learner actually has right now.
    """
    stats = lesson_service.get_stats(db, user_id)
    db.commit()
    return _stats_payload(db, stats)


@router.get("/{user_id}/profile", response_model=UserProfileRead)
def read_user_profile(user_id: int, db: Session = Depends(get_db)) -> UserProfileRead:
    """Identity, stats, badge progress and the last two weeks of activity."""
    user = db.get(User, user_id)
    if user is None:
        raise NotFoundError("User not found")
    stats = lesson_service.get_stats(db, user_id)
    db.commit()

    rows = db.execute(
        select(Achievement, UserAchievement)
        .outerjoin(
            UserAchievement,
            (UserAchievement.achievement_id == Achievement.id)
            & (UserAchievement.user_id == user_id),
        )
        .order_by(Achievement.id)
    ).all()

    activity = db.scalars(
        select(DailyXp)
        .where(DailyXp.user_id == user_id, DailyXp.date >= clock.today() - timedelta(days=13))
        .order_by(DailyXp.date)
    ).all()

    return UserProfileRead(
        user=UserRead.model_validate(user),
        stats=_stats_payload(db, stats),
        total_crowns=db.scalar(
            select(func.coalesce(func.sum(UserProgress.crowns), 0)).where(
                UserProgress.user_id == user_id
            )
        )
        or 0,
        lessons_completed=db.scalar(
            select(func.count(LessonAttempt.id)).where(
                LessonAttempt.user_id == user_id, LessonAttempt.is_completed.is_(True)
            )
        )
        or 0,
        achievements=[
            AchievementRead(
                code=achievement.code,
                title=achievement.title,
                description=achievement.description,
                icon=achievement.icon,
                color_hex=achievement.color_hex,
                target=achievement.target,
                progress=progress.progress if progress else 0,
                unlocked_at=progress.unlocked_at if progress else None,
            )
            for achievement, progress in rows
        ],
        recent_activity=[DailyXpRead.model_validate(row) for row in activity],
    )


@router.post("/{user_id}/hearts/refill", response_model=UserStatsRead)
def refill_hearts(user_id: int, db: Session = Depends(get_db)) -> UserStatsRead:
    """Spend gems to refill the heart bar.

    Mocked economy: gems are only ever granted by the seed, so this is the one
    place they are spent.
    """
    stats = lesson_service.refill_hearts_with_gems(db, user_id)
    return _stats_payload(db, stats)
