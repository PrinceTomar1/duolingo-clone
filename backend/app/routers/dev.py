"""Developer-only endpoints for demonstrating time-dependent behaviour.

Streaks and heart regeneration are the two rules that would otherwise take days
to show working. These endpoints move one learner's own simulated clock so the
whole thing is demonstrable in a few seconds -- without moving anyone else's.

Mounted only when ``DEBUG`` is true -- in a deployed configuration the router is
never registered, so the routes do not exist at all rather than merely
returning 403.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core import clock
from app.core.database import get_db
from app.models.stats import UserStats
from app.models.user import User
from app.services import gamification_service
from app.services.exceptions import NotFoundError

router = APIRouter(prefix="/dev", tags=["dev"])


class AdvanceRequest(BaseModel):
    """Which learner's clock to move, and how far."""

    user_id: int
    days: int = Field(default=1, ge=0, le=365)
    minutes: int = Field(default=0, ge=0, le=60 * 24 * 365)


class ResetRequest(BaseModel):
    """Which learner's clock to drop back to real time."""

    user_id: int


class ClockRead(BaseModel):
    """Where one learner's simulated clock now stands."""

    user_id: int
    username: str
    simulated_now: str
    simulated_today: str
    offset_seconds: int
    current_streak: int


def _load_stats(db: Session, user_id: int) -> tuple[User, UserStats]:
    user = db.get(User, user_id)
    if user is None:
        raise NotFoundError("User not found")
    stats = db.get(UserStats, user_id)
    if stats is None:
        raise NotFoundError("User not found")
    return user, stats


def _snapshot(db: Session, user: User, stats: UserStats) -> ClockRead:
    """Recompute this one learner's streak under their new clock and report it.

    Scoped to the single learner whose offset just changed -- the previous
    version of this endpoint recomputed *every* learner's streak on every call,
    which was itself a symptom of the clock being process-global rather than
    per learner.
    """
    moment = clock.now_for(stats.clock_offset_seconds)
    gamification_service.refresh_streak(db, stats, moment.date())
    db.commit()
    return ClockRead(
        user_id=user.id,  # type: ignore[arg-type]
        username=user.username,  # type: ignore[arg-type]
        simulated_now=moment.isoformat(timespec="seconds"),
        simulated_today=moment.date().isoformat(),
        offset_seconds=stats.clock_offset_seconds,
        current_streak=stats.current_streak,
    )


@router.post("/advance-day", response_model=ClockRead)
def advance_day(body: AdvanceRequest, db: Session = Depends(get_db)) -> ClockRead:
    """Move one learner's time forward, then refresh their derived streak.

    Advancing one day without practising is what makes the streak rule
    visible: that learner's run survives one quiet day and collapses on the
    second, exactly as ``compute_streak`` specifies. The offset is stored on
    that learner's own ``user_stats`` row, so no other learner's clock moves
    and a server restart does not undo it.
    """
    user, stats = _load_stats(db, body.user_id)
    stats.clock_offset_seconds += body.days * 86400 + body.minutes * 60
    return _snapshot(db, user, stats)


@router.post("/reset-clock", response_model=ClockRead)
def reset_clock(body: ResetRequest, db: Session = Depends(get_db)) -> ClockRead:
    """Drop one learner's simulated offset and return them to real time."""
    user, stats = _load_stats(db, body.user_id)
    stats.clock_offset_seconds = 0
    return _snapshot(db, user, stats)
