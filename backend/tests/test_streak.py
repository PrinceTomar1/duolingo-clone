"""Streak derivation from the daily-XP ledger."""

from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models.stats import UserStats
from app.models.user import User
from app.services import gamification_service as gamification

TODAY = date(2026, 3, 15)


def days_ago(*offsets: int) -> set[date]:
    """Helper: the set of days that many days before ``TODAY``."""
    return {TODAY - timedelta(days=offset) for offset in offsets}


class TestComputeStreak:
    """``compute_streak`` is pure: a set of active days in, a length out."""

    def test_no_activity_is_no_streak(self) -> None:
        assert gamification.compute_streak(set(), TODAY) == 0

    def test_single_day_today(self) -> None:
        assert gamification.compute_streak(days_ago(0), TODAY) == 1

    def test_consecutive_run_ending_today(self) -> None:
        assert gamification.compute_streak(days_ago(0, 1, 2, 3, 4, 5, 6), TODAY) == 7

    def test_streak_survives_a_day_not_yet_practised(self) -> None:
        """Ending yesterday still counts -- today is not over yet."""
        assert gamification.compute_streak(days_ago(1, 2, 3), TODAY) == 3

    def test_gap_of_more_than_one_day_resets(self) -> None:
        assert gamification.compute_streak(days_ago(2, 3, 4), TODAY) == 0

    def test_only_the_run_touching_today_counts(self) -> None:
        """An old ten-day run does not add to the current two-day one."""
        active = days_ago(0, 1) | days_ago(5, 6, 7, 8, 9, 10)
        assert gamification.compute_streak(active, TODAY) == 2

    def test_future_rows_do_not_extend_the_streak(self) -> None:
        active = days_ago(0, 1) | {TODAY + timedelta(days=1)}
        assert gamification.compute_streak(active, TODAY) == 2


class TestLedgerDrivenStreak:
    def test_first_lesson_of_the_day_starts_a_streak(self, db: Session, user: User) -> None:
        gamification.record_daily_xp(db, user.id, 15, TODAY)
        db.flush()
        stats = db.get(UserStats, user.id)
        gamification.refresh_streak(db, stats, TODAY)
        assert stats.current_streak == 1

    def test_second_lesson_same_day_does_not_bump_the_streak(
        self, db: Session, user: User
    ) -> None:
        gamification.record_daily_xp(db, user.id, 15, TODAY)
        gamification.record_daily_xp(db, user.id, 25, TODAY)
        db.flush()
        stats = db.get(UserStats, user.id)
        gamification.refresh_streak(db, stats, TODAY)
        assert stats.current_streak == 1
        # Both awards land on the one ledger row for that day.
        assert gamification.xp_earned_on(db, user.id, TODAY) == 40

    def test_consecutive_days_increment(self, db: Session, user: User) -> None:
        stats = db.get(UserStats, user.id)
        for offset in (2, 1, 0):
            gamification.record_daily_xp(db, user.id, 10, TODAY - timedelta(days=offset))
            db.flush()
            gamification.refresh_streak(db, stats, TODAY - timedelta(days=offset))
        assert stats.current_streak == 3

    def test_streak_resets_after_a_missed_day(self, db: Session, user: User) -> None:
        gamification.record_daily_xp(db, user.id, 10, TODAY - timedelta(days=5))
        gamification.record_daily_xp(db, user.id, 10, TODAY - timedelta(days=4))
        gamification.record_daily_xp(db, user.id, 10, TODAY)
        db.flush()
        stats = db.get(UserStats, user.id)
        gamification.refresh_streak(db, stats, TODAY)
        assert stats.current_streak == 1

    def test_longest_streak_is_a_high_water_mark(self, db: Session, user: User) -> None:
        stats = db.get(UserStats, user.id)
        for offset in (6, 5, 4):
            gamification.record_daily_xp(db, user.id, 10, TODAY - timedelta(days=offset))
        db.flush()
        gamification.refresh_streak(db, stats, TODAY - timedelta(days=4))
        assert stats.longest_streak == 3

        gamification.record_daily_xp(db, user.id, 10, TODAY)
        db.flush()
        gamification.refresh_streak(db, stats, TODAY)
        assert stats.current_streak == 1
        assert stats.longest_streak == 3

    def test_last_active_date_tracks_the_newest_ledger_row(
        self, db: Session, user: User
    ) -> None:
        gamification.record_daily_xp(db, user.id, 10, TODAY - timedelta(days=3))
        gamification.record_daily_xp(db, user.id, 10, TODAY)
        db.flush()
        stats = db.get(UserStats, user.id)
        gamification.refresh_streak(db, stats, TODAY)
        assert stats.last_active_date == TODAY


class TestWeeklyXp:
    def test_sums_only_days_in_range(self, db: Session, user: User) -> None:
        for offset, amount in ((0, 30), (3, 20), (9, 100)):
            gamification.record_daily_xp(db, user.id, amount, TODAY - timedelta(days=offset))
        db.flush()
        week_start = TODAY - timedelta(days=6)
        assert gamification.xp_earned_since(db, user.id, week_start) == 50
