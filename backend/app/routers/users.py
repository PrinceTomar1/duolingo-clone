"""Learner identity, stats, profile and heart refills."""

from datetime import timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core import clock, rate_limit
from app.core.config import settings
from app.core.database import get_db
from app.core.security import hash_password, verify_password
from app.models.achievement import Achievement, UserAchievement
from app.models.progress import LessonAttempt, UserProgress
from app.models.stats import DailyXp, UserStats
from app.models.user import User
from app.schemas.user import (
    AchievementRead,
    DailyXpRead,
    UserAuthenticate,
    UserCreate,
    UserProfileRead,
    UserRead,
    UserStatsRead,
)
from app.services import gamification_service, lesson_service
from app.services.exceptions import (
    ConflictError,
    NotFoundError,
    TooManyAttemptsError,
    UnauthorizedError,
)

router = APIRouter(prefix="/users", tags=["users"])


def _stats_payload(db: Session, stats: UserStats) -> UserStatsRead:
    """Assemble the stats response, including the two derived heart fields."""
    today = clock.today_for(stats.clock_offset_seconds)
    return UserStatsRead(
        user_id=stats.user_id,
        total_xp=stats.total_xp,
        current_streak=stats.current_streak,
        longest_streak=stats.longest_streak,
        last_active_date=stats.last_active_date,
        hearts=stats.hearts,
        max_hearts=settings.max_hearts,
        seconds_until_next_heart=gamification_service.seconds_until_next_heart(
            stats, clock.now_for(stats.clock_offset_seconds)
        ),
        gems=stats.gems,
        heart_refill_gem_cost=settings.heart_refill_gem_cost,
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


@router.post("", response_model=UserRead, status_code=201)
def create_user(body: UserCreate, db: Session = Depends(get_db)) -> User:
    """Add a new learner: "Switch learner" -> "Add a new learner" asks for this.

    A real signup form's entire job in a build with no required auth: pick a
    name, get a fresh account. The new learner starts exactly where the seeded
    ones did on day one -- a full heart bar, no XP, no streak, no gems (Duolingo
    does not hand out currency at signup either) -- because inventing more
    would misrepresent what a brand new account actually has. A password is
    optional (see ``UserCreate``); when set, it is hashed here and never
    handled anywhere else in plaintext.
    """
    username = body.username.strip().lower()
    if db.scalar(select(User).where(User.username == username)) is not None:
        raise ConflictError("That username is already taken.")

    user = User(
        username=username,
        display_name=body.display_name.strip(),
        password_hash=hash_password(body.password) if body.password else None,
    )
    db.add(user)
    db.flush()  # Assigns user.id before UserStats references it.
    db.add(
        UserStats(
            user_id=user.id,
            hearts=settings.max_hearts,
            hearts_updated_at=clock.now_for(0),
            daily_goal_xp=settings.default_daily_goal_xp,
        )
    )
    db.commit()
    db.refresh(user)
    return user


@router.post("/authenticate", response_model=UserRead)
def authenticate_user(body: UserAuthenticate, db: Session = Depends(get_db)) -> User:
    """Switch into a password-protected learner.

    The only endpoint in the app that takes a password. A passwordless
    (seeded, or created-without-one) learner is never reachable through here
    on purpose -- switching into those stays the instant, no-password flow it
    always was; this exists only for the learners that opted into a password
    at creation. Wrong username and wrong password both answer 401, not 404 vs
    401, so a caller cannot use this endpoint to discover which usernames exist.

    Rate-limited per username (see ``core.rate_limit``): this is the one
    endpoint in the app that checks a secret against a stored value, which
    makes it the one endpoint worth protecting from being hammered.
    """
    username = body.username.strip().lower()
    if rate_limit.is_locked_out(username):
        raise TooManyAttemptsError(
            "Too many attempts for this learner. Wait a few minutes and try again."
        )

    user = db.scalar(select(User).where(User.username == username))
    if user is None or user.password_hash is None or not verify_password(
        body.password, user.password_hash
    ):
        rate_limit.register_failure(username)
        raise UnauthorizedError("Incorrect username or password.")

    rate_limit.clear(username)
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
        .where(
            DailyXp.user_id == user_id,
            DailyXp.date >= clock.today_for(stats.clock_offset_seconds) - timedelta(days=13),
        )
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
