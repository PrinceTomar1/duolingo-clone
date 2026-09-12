"""Response models for learner identity, stats and profile."""

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class UserRead(ORMModel):
    """Public identity of a learner.

    ``has_password`` -- never the hash itself -- is what the switcher uses to
    decide whether picking this learner needs a password prompt or can switch
    instantly, the same way it always has for the passwordless seeded accounts.
    """

    id: int
    username: str
    display_name: str
    avatar_color: str
    has_password: bool
    created_at: datetime


class UserCreate(BaseModel):
    """What "Add a new learner" actually asks for.

    ``password`` is optional: there is no required auth in this build (the
    assignment explicitly accepts simplified auth), so a blank password keeps
    the account exactly as instant-switchable as every seeded one. Set one and
    the account is real in the one sense that matters -- nobody switches into
    it without knowing it. Length limits mirror the ``users`` table columns so
    a request that would fail the database constraint fails validation first,
    with a message naming the field.
    """

    username: str = Field(min_length=2, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    display_name: str = Field(min_length=1, max_length=100)
    password: str | None = Field(default=None, min_length=8, max_length=100)


class UserAuthenticate(BaseModel):
    """What switching into a password-protected learner asks for."""

    username: str
    password: str


class UserStatsRead(BaseModel):
    """The numbers on the right rail: hearts, streak, gems, daily goal."""

    user_id: int
    total_xp: int
    current_streak: int
    longest_streak: int
    last_active_date: date | None
    hearts: int
    max_hearts: int
    seconds_until_next_heart: int | None = Field(
        default=None, description="None when the heart bar is already full"
    )
    gems: int
    # Sent so the UI never has to hardcode the price. It is a server rule, and a
    # copy in the client can advertise a cost the server does not charge.
    heart_refill_gem_cost: int
    daily_goal_xp: int
    daily_xp_earned: int
    weekly_xp: int


class AchievementRead(BaseModel):
    """A badge with this learner's progress against it."""

    code: str
    title: str
    description: str
    icon: str
    color_hex: str
    target: int
    progress: int
    unlocked_at: datetime | None


class DailyXpRead(ORMModel):
    """One day of the ledger, for the profile activity chart."""

    date: date
    xp_earned: int


class UserProfileRead(BaseModel):
    """The profile page payload: identity, stats, badges and recent activity."""

    user: UserRead
    stats: UserStatsRead
    total_crowns: int
    lessons_completed: int
    achievements: list[AchievementRead]
    recent_activity: list[DailyXpRead]
