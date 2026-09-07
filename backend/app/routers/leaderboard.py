"""Weekly leaderboard."""

from datetime import timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core import clock
from app.core.database import get_db
from app.models.stats import DailyXp, UserStats
from app.models.user import User
from app.schemas.leaderboard import LeaderboardEntry, LeaderboardRead

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])


@router.get("", response_model=LeaderboardRead)
def read_leaderboard(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> LeaderboardRead:
    """Rank learners by XP earned in the last seven days.

    A single grouped query with an outer join, so a learner with no activity
    this week still appears (with zero) rather than vanishing from the league.
    Ties break on all-time XP, then username, so the order is stable between
    requests.
    """
    week_start = clock.today() - timedelta(days=6)
    weekly_xp = func.coalesce(func.sum(DailyXp.xp_earned), 0).label("weekly_xp")

    rows = db.execute(
        select(User, UserStats, weekly_xp)
        .join(UserStats, UserStats.user_id == User.id)
        .outerjoin(DailyXp, (DailyXp.user_id == User.id) & (DailyXp.date >= week_start))
        .group_by(User.id)
        .order_by(weekly_xp.desc(), UserStats.total_xp.desc(), User.username)
        .limit(limit)
    ).all()

    return LeaderboardRead(
        week_start=week_start,
        week_end=clock.today(),
        entries=[
            LeaderboardEntry(
                rank=rank,
                user_id=user.id,
                username=user.username,
                display_name=user.display_name,
                avatar_color=user.avatar_color,
                weekly_xp=int(weekly),
                total_xp=stats.total_xp,
                current_streak=stats.current_streak,
            )
            for rank, (user, stats, weekly) in enumerate(rows, start=1)
        ],
    )
