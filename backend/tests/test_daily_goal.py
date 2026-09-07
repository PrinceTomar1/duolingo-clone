"""The daily XP goal: today's ledger row, and what happens when the day turns.

The goal ring is driven by ``daily_xp``, not by a counter on ``user_stats``, so
these tests pin the two properties that ring depends on: everything earned today
lands on exactly one row, and tomorrow starts from zero without touching the
learner's lifetime total.
"""

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import clock
from app.models.course import Course
from app.models.stats import DailyXp, UserStats
from app.models.user import User
from app.services import gamification_service as gamification
from tests.test_xp import first_lesson, play


class TestDailyLedger:
    """``record_daily_xp`` upserts one row per learner per day."""

    def test_a_new_day_starts_at_zero(self, db: Session, user: User) -> None:
        assert gamification.xp_earned_on(db, user.id, clock.today()) == 0

    def test_two_awards_on_one_day_share_a_single_row(self, db: Session, user: User) -> None:
        today = clock.today()
        gamification.record_daily_xp(db, user.id, 15, today)
        gamification.record_daily_xp(db, user.id, 10, today)
        db.commit()

        rows = db.scalars(
            select(DailyXp).where(DailyXp.user_id == user.id, DailyXp.date == today)
        ).all()
        assert len(rows) == 1, "the UNIQUE(user_id, date) constraint means this must upsert"
        assert rows[0].xp_earned == 25

    def test_each_day_keeps_its_own_total(self, db: Session, user: User) -> None:
        today = clock.today()
        yesterday = today - timedelta(days=1)
        gamification.record_daily_xp(db, user.id, 40, yesterday)
        gamification.record_daily_xp(db, user.id, 15, today)
        db.commit()

        assert gamification.xp_earned_on(db, user.id, yesterday) == 40
        assert gamification.xp_earned_on(db, user.id, today) == 15

    def test_a_day_with_no_activity_reports_zero(self, db: Session, user: User) -> None:
        gamification.record_daily_xp(db, user.id, 20, clock.today())
        db.commit()
        assert gamification.xp_earned_on(db, user.id, date(2000, 1, 1)) == 0


class TestGoalProgress:
    """What the ring shows after real lessons, and across a day boundary."""

    def test_completing_a_lesson_fills_the_ring(
        self, db: Session, course: Course, user: User
    ) -> None:
        stats = db.get(UserStats, user.id)
        assert gamification.xp_earned_on(db, user.id, clock.today()) == 0

        summary = play(db, user, first_lesson(db, course))

        assert summary.daily_xp_earned == summary.xp_earned
        assert summary.daily_goal_xp == stats.daily_goal_xp
        assert gamification.xp_earned_on(db, user.id, clock.today()) == summary.xp_earned

    def test_the_goal_can_be_met_and_exceeded(
        self, db: Session, course: Course, user: User
    ) -> None:
        stats = db.get(UserStats, user.id)
        summary = play(db, user, first_lesson(db, course))
        # A perfect first lesson pays 25 against the seeded 20-XP goal.
        assert summary.daily_xp_earned >= stats.daily_goal_xp

    def test_the_ring_resets_tomorrow_but_total_xp_does_not(
        self, db: Session, course: Course, user: User
    ) -> None:
        summary = play(db, user, first_lesson(db, course))
        earned_today = summary.daily_xp_earned
        assert earned_today > 0

        clock.advance(days=1)

        assert gamification.xp_earned_on(db, user.id, clock.today()) == 0, (
            "a new day starts the ring at zero"
        )
        stats = db.get(UserStats, user.id)
        assert stats.total_xp == summary.total_xp, "the lifetime total is unaffected by the date"

    def test_yesterdays_xp_is_still_readable_after_the_day_turns(
        self, db: Session, course: Course, user: User
    ) -> None:
        summary = play(db, user, first_lesson(db, course))
        yesterday = clock.today()
        clock.advance(days=1)

        assert gamification.xp_earned_on(db, user.id, yesterday) == summary.daily_xp_earned
