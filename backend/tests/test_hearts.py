"""Heart depletion, lazy regeneration and gem refills."""

from datetime import datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.stats import UserStats
from app.models.user import User
from app.services import gamification_service as gamification

NOON = datetime(2026, 1, 1, 12, 0)


class TestRegeneration:
    """``regenerated_hearts`` is pure, so every case is a direct assertion."""

    def test_full_bar_never_exceeds_the_maximum(self) -> None:
        hearts, anchor = gamification.regenerated_hearts(5, NOON - timedelta(days=3), NOON)
        assert hearts == settings.max_hearts
        assert anchor == NOON

    def test_nothing_regenerates_before_one_full_interval(self) -> None:
        hearts, anchor = gamification.regenerated_hearts(2, NOON - timedelta(minutes=29), NOON)
        assert hearts == 2
        assert anchor == NOON - timedelta(minutes=29)

    def test_one_heart_per_interval(self) -> None:
        hearts, _ = gamification.regenerated_hearts(0, NOON - timedelta(minutes=90), NOON)
        assert hearts == 3

    def test_partial_interval_is_not_discarded(self) -> None:
        """75 minutes buys two hearts and banks the leftover 15."""
        hearts, anchor = gamification.regenerated_hearts(1, NOON - timedelta(minutes=75), NOON)
        assert hearts == 3
        assert anchor == NOON - timedelta(minutes=15)

    def test_regeneration_caps_at_the_maximum(self) -> None:
        hearts, anchor = gamification.regenerated_hearts(1, NOON - timedelta(days=1), NOON)
        assert hearts == settings.max_hearts
        assert anchor == NOON

    def test_clock_moving_backwards_is_ignored(self) -> None:
        hearts, anchor = gamification.regenerated_hearts(2, NOON, NOON - timedelta(hours=1))
        assert hearts == 2
        assert anchor == NOON


class TestDepletion:
    def test_each_wrong_answer_costs_one_heart(self, db: Session, user: User) -> None:
        stats = db.get(UserStats, user.id)
        for expected in (4, 3, 2, 1, 0):
            gamification.lose_heart(stats, NOON)
            assert stats.hearts == expected

    def test_hearts_never_go_negative(self, db: Session, user: User) -> None:
        stats = db.get(UserStats, user.id)
        for _ in range(8):
            gamification.lose_heart(stats, NOON)
        assert stats.hearts == 0

    def test_first_loss_from_a_full_bar_starts_the_regen_timer(
        self, db: Session, user: User
    ) -> None:
        stats = db.get(UserStats, user.id)
        stats.hearts_updated_at = NOON - timedelta(days=5)
        gamification.lose_heart(stats, NOON)
        assert stats.hearts == 4
        assert stats.hearts_updated_at == NOON

    def test_seconds_until_next_heart_counts_down(self, db: Session, user: User) -> None:
        stats = db.get(UserStats, user.id)
        gamification.lose_heart(stats, NOON)
        assert gamification.seconds_until_next_heart(stats, NOON) == 30 * 60
        assert gamification.seconds_until_next_heart(stats, NOON + timedelta(minutes=10)) == 20 * 60

    def test_no_countdown_when_the_bar_is_full(self, db: Session, user: User) -> None:
        stats = db.get(UserStats, user.id)
        assert gamification.seconds_until_next_heart(stats, NOON) is None


class TestGemRefill:
    def test_refill_charges_gems_and_fills_the_bar(self, db: Session, user: User) -> None:
        stats = db.get(UserStats, user.id)
        stats.hearts = 0
        stats.hearts_updated_at = NOON
        assert gamification.refill_hearts(stats, NOON) is True
        assert stats.hearts == settings.max_hearts
        assert stats.gems == 500 - settings.heart_refill_gem_cost

    def test_refill_refused_when_gems_are_short(self, db: Session, user: User) -> None:
        stats = db.get(UserStats, user.id)
        stats.hearts = 1
        stats.gems = 10
        assert gamification.refill_hearts(stats, NOON) is False
        assert stats.gems == 10
        assert stats.hearts == 1

    def test_refill_refused_when_already_full(self, db: Session, user: User) -> None:
        stats = db.get(UserStats, user.id)
        assert gamification.refill_hearts(stats, NOON) is False
        assert stats.gems == 500


@pytest.mark.parametrize("minutes", [0, 15, 30, 59, 60, 600])
def test_regeneration_is_monotonic(minutes: int) -> None:
    """More elapsed time can never mean fewer hearts."""
    hearts, _ = gamification.regenerated_hearts(0, NOON - timedelta(minutes=minutes), NOON)
    baseline, _ = gamification.regenerated_hearts(0, NOON, NOON)
    assert hearts >= baseline
