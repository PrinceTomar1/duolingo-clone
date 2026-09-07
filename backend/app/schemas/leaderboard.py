"""Response models for the weekly leaderboard."""

from datetime import date

from pydantic import BaseModel


class LeaderboardEntry(BaseModel):
    """One row in the league table."""

    rank: int
    user_id: int
    username: str
    display_name: str
    avatar_color: str
    weekly_xp: int
    total_xp: int
    current_streak: int


class LeaderboardRead(BaseModel):
    """The league table plus the window it was computed over.

    Ranking on the last seven days rather than all-time XP is what makes a
    league competitive: a learner who joined yesterday can still place.
    """

    week_start: date
    week_end: date
    entries: list[LeaderboardEntry]
