"""Developer-only endpoints for demonstrating time-dependent behaviour.

Streaks and heart regeneration are the two rules that would otherwise take days
to show working. These endpoints move the application's simulated clock so the
whole thing is demonstrable in a few seconds.

Mounted only when ``DEBUG`` is true -- in a deployed configuration the router is
never registered, so the routes do not exist at all rather than merely
returning 403.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import clock
from app.core.database import get_db
from app.models.stats import UserStats
from app.models.user import User
from app.services import gamification_service

router = APIRouter(prefix="/dev", tags=["dev"])


class AdvanceRequest(BaseModel):
    """How far to move the simulated clock."""

    days: int = Field(default=1, ge=0, le=365)
    minutes: int = Field(default=0, ge=0, le=60 * 24 * 365)


class ClockRead(BaseModel):
    """Where the simulated clock now stands, and its effect on the demo learner."""

    simulated_now: str
    simulated_today: str
    offset_seconds: int
    streaks: dict[str, int]


def _snapshot(db: Session) -> ClockRead:
    """Recompute every learner's streak under the new clock and report it."""
    for stats in db.scalars(select(UserStats)).all():
        gamification_service.refresh_streak(db, stats)
    db.commit()

    streaks = {
        user.username: stats.current_streak
        for user, stats in db.execute(
            select(User, UserStats).join(UserStats, UserStats.user_id == User.id)
        ).all()
    }
    return ClockRead(
        simulated_now=clock.now().isoformat(timespec="seconds"),
        simulated_today=clock.today().isoformat(),
        offset_seconds=int(clock.offset().total_seconds()),
        streaks=streaks,
    )


@router.post("/advance-day", response_model=ClockRead)
def advance_day(body: AdvanceRequest, db: Session = Depends(get_db)) -> ClockRead:
    """Move time forward, then refresh every learner's derived streak.

    Advancing one day without anyone practising is what makes the streak rule
    visible: the demo learner's run survives one quiet day and collapses on the
    second, exactly as ``compute_streak`` specifies.
    """
    clock.advance(days=body.days, minutes=body.minutes)
    return _snapshot(db)


@router.post("/reset-clock", response_model=ClockRead)
def reset_clock(db: Session = Depends(get_db)) -> ClockRead:
    """Drop the simulated offset and return to real time."""
    clock.reset()
    return _snapshot(db)
