"""HTTP-level tests: status codes, payload shape and the answer-leak guarantee."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.main import app
from app.models.course import Course, Skill, Unit
from app.models.lesson import Lesson
from app.models.user import User


@pytest.fixture
def client(db: Session, course: Course, user: User) -> TestClient:
    """A test client whose requests share the test's session.

    Overriding ``get_db`` is the whole reason routers take the session as a
    dependency rather than importing ``SessionLocal`` themselves.
    """
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def first_lesson_id(db: Session, course: Course) -> int:
    unit = db.scalars(select(Unit).where(Unit.course_id == course.id).order_by(Unit.order_index)).first()
    skill = db.scalars(select(Skill).where(Skill.unit_id == unit.id).order_by(Skill.order_index)).first()
    return db.scalars(
        select(Lesson).where(Lesson.skill_id == skill.id).order_by(Lesson.order_index)
    ).first().id


class TestMeta:
    def test_health(self, client: TestClient) -> None:
        assert client.get("/health").json() == {"status": "ok"}

    def test_openapi_schema_is_generated(self, client: TestClient) -> None:
        paths = client.get("/openapi.json").json()["paths"]
        assert "/api/v1/course/path" in paths
        assert "/api/v1/attempts/{attempt_id}/answer" in paths


class TestCoursePath:
    def test_returns_units_with_derived_state(self, client: TestClient, user: User) -> None:
        body = client.get("/api/v1/course/path", params={"user_id": user.id}).json()
        assert body["from_language"] == "English"
        assert len(body["units"]) == 2
        assert body["units"][0]["skills"][0]["state"] == "available"
        assert body["units"][0]["skills"][1]["state"] == "locked"

    def test_user_id_is_required(self, client: TestClient) -> None:
        assert client.get("/api/v1/course/path").status_code == 422


class TestLessonFetch:
    def test_never_returns_the_answer_key(
        self, client: TestClient, db: Session, course: Course
    ) -> None:
        """The single most important assertion in the suite."""
        response = client.get("/api/v1/lessons/{}".format(first_lesson_id(db, course)))
        assert response.status_code == 200
        raw = response.text
        assert "correct_answer" not in raw
        assert "explanation" not in raw
        assert "accepted" not in raw

    def test_returns_every_exercise_in_order(
        self, client: TestClient, db: Session, course: Course
    ) -> None:
        body = client.get("/api/v1/lessons/{}".format(first_lesson_id(db, course))).json()
        assert len(body["exercises"]) == 9
        assert [item["order_index"] for item in body["exercises"]] == list(range(9))
        assert {item["type"] for item in body["exercises"]} == {
            "MULTIPLE_CHOICE",
            "MATCH_PAIRS",
            "TRANSLATE_WORD_BANK",
            "FILL_BLANK",
            "TYPE_ANSWER",
        }

    def test_missing_lesson_is_404(self, client: TestClient) -> None:
        response = client.get("/api/v1/lessons/99999")
        assert response.status_code == 404
        assert response.json()["error"] == "NotFoundError"


class TestAttemptFlow:
    def test_start_answer_complete(
        self, client: TestClient, db: Session, course: Course, user: User
    ) -> None:
        lesson_id = first_lesson_id(db, course)
        start = client.post(
            "/api/v1/lessons/{}/start".format(lesson_id), json={"user_id": user.id}
        )
        assert start.status_code == 201
        attempt_id = start.json()["attempt_id"]
        assert start.json()["hearts_remaining"] == 5

        lesson = client.get("/api/v1/lessons/{}".format(lesson_id)).json()
        exercise = next(
            item for item in lesson["exercises"] if item["type"] == "MULTIPLE_CHOICE"
        )
        wrong = client.post(
            "/api/v1/attempts/{}/answer".format(attempt_id),
            json={"exercise_id": exercise["id"], "answer": {"choice": "not an option"}},
        ).json()
        assert wrong["is_correct"] is False
        assert wrong["hearts_remaining"] == 4
        assert wrong["correct_answer"] in exercise["payload"]["options"]

        right = client.post(
            "/api/v1/attempts/{}/answer".format(attempt_id),
            json={"exercise_id": exercise["id"], "answer": {"choice": wrong["correct_answer"]}},
        ).json()
        assert right["is_correct"] is True
        assert right["hearts_remaining"] == 4

        summary = client.post("/api/v1/attempts/{}/complete".format(attempt_id))
        assert summary.status_code == 200
        assert summary.json()["crown_earned"] is True
        assert summary.json()["xp_earned"] > 0

    def test_starting_a_locked_lesson_is_403(
        self, client: TestClient, db: Session, course: Course, user: User
    ) -> None:
        unit = db.scalars(
            select(Unit).where(Unit.course_id == course.id).order_by(Unit.order_index)
        ).first()
        locked_skill = db.scalars(
            select(Skill).where(Skill.unit_id == unit.id).order_by(Skill.order_index)
        ).all()[1]
        response = client.post(
            "/api/v1/lessons/{}/start".format(locked_skill.lessons[0].id),
            json={"user_id": user.id},
        )
        assert response.status_code == 403
        assert response.json()["error"] == "SkillLockedError"

    def test_completing_twice_is_409(
        self, client: TestClient, db: Session, course: Course, user: User
    ) -> None:
        lesson_id = first_lesson_id(db, course)
        attempt_id = client.post(
            "/api/v1/lessons/{}/start".format(lesson_id), json={"user_id": user.id}
        ).json()["attempt_id"]
        client.post("/api/v1/attempts/{}/complete".format(attempt_id))
        again = client.post("/api/v1/attempts/{}/complete".format(attempt_id))
        assert again.status_code == 409


class TestUsers:
    def test_stats_shape(self, client: TestClient, user: User) -> None:
        body = client.get("/api/v1/users/{}/stats".format(user.id)).json()
        assert body["hearts"] == 5
        assert body["max_hearts"] == 5
        assert body["seconds_until_next_heart"] is None
        assert body["daily_xp_earned"] == 0

    def test_profile_includes_every_achievement(self, client: TestClient, user: User) -> None:
        body = client.get("/api/v1/users/{}/profile".format(user.id)).json()
        assert body["user"]["username"] == "tester"
        assert len(body["achievements"]) == 6
        assert all(item["unlocked_at"] is None for item in body["achievements"])

    def test_lookup_by_username(self, client: TestClient) -> None:
        assert client.get("/api/v1/users/by-username/tester").json()["username"] == "tester"

    def test_unknown_username_is_404(self, client: TestClient) -> None:
        assert client.get("/api/v1/users/by-username/nobody").status_code == 404

    def test_refill_with_a_full_bar_is_409(self, client: TestClient, user: User) -> None:
        assert client.post("/api/v1/users/{}/hearts/refill".format(user.id)).status_code == 409


class TestLeaderboard:
    def test_ranks_learners_and_includes_the_inactive(
        self, client: TestClient, user: User
    ) -> None:
        body = client.get("/api/v1/leaderboard").json()
        assert body["entries"][0]["rank"] == 1
        assert body["entries"][0]["username"] == "tester"
        assert body["entries"][0]["weekly_xp"] == 0

    def test_limit_is_validated(self, client: TestClient) -> None:
        assert client.get("/api/v1/leaderboard", params={"limit": 0}).status_code == 422


class TestDevEndpoints:
    def test_advancing_a_day_reports_the_simulated_date(self, client: TestClient) -> None:
        from app.core import clock

        before = clock.today()
        body = client.post("/api/v1/dev/advance-day", json={"days": 3}).json()
        assert body["simulated_today"] != before.isoformat()
        assert body["offset_seconds"] == 3 * 24 * 3600
        client.post("/api/v1/dev/reset-clock")


class TestMatchPairCheck:
    """The per-pair check that lets the match board give live feedback."""

    def _match_exercise(self, client: TestClient, lesson_id: int) -> dict:
        lesson = client.get("/api/v1/lessons/{}".format(lesson_id)).json()
        return next(item for item in lesson["exercises"] if item["type"] == "MATCH_PAIRS")

    def test_correct_pair_is_confirmed_and_costs_no_heart(
        self, client: TestClient, db: Session, course: Course, user: User
    ) -> None:
        from app.models.lesson import Exercise

        lesson_id = first_lesson_id(db, course)
        attempt_id = client.post(
            "/api/v1/lessons/{}/start".format(lesson_id), json={"user_id": user.id}
        ).json()["attempt_id"]
        exercise = self._match_exercise(client, lesson_id)
        key = db.get(Exercise, exercise["id"]).correct_answer["pairs"]
        left, right = next(iter(key.items()))

        response = client.post(
            "/api/v1/attempts/{}/match-pair".format(attempt_id),
            json={"exercise_id": exercise["id"], "left": left, "right": right},
        )
        assert response.json() == {"is_correct": True}
        assert client.get("/api/v1/users/{}/stats".format(user.id)).json()["hearts"] == 5

    def test_wrong_pair_is_rejected_without_revealing_the_answer(
        self, client: TestClient, db: Session, course: Course, user: User
    ) -> None:
        lesson_id = first_lesson_id(db, course)
        attempt_id = client.post(
            "/api/v1/lessons/{}/start".format(lesson_id), json={"user_id": user.id}
        ).json()["attempt_id"]
        exercise = self._match_exercise(client, lesson_id)

        response = client.post(
            "/api/v1/attempts/{}/match-pair".format(attempt_id),
            json={
                "exercise_id": exercise["id"],
                "left": exercise["payload"]["left"][0],
                "right": "not a real translation",
            },
        )
        assert response.json() == {"is_correct": False}
        assert set(response.json()) == {"is_correct"}

    def test_non_match_exercise_is_rejected(
        self, client: TestClient, db: Session, course: Course, user: User
    ) -> None:
        lesson_id = first_lesson_id(db, course)
        attempt_id = client.post(
            "/api/v1/lessons/{}/start".format(lesson_id), json={"user_id": user.id}
        ).json()["attempt_id"]
        lesson = client.get("/api/v1/lessons/{}".format(lesson_id)).json()
        choice = next(item for item in lesson["exercises"] if item["type"] == "MULTIPLE_CHOICE")
        response = client.post(
            "/api/v1/attempts/{}/match-pair".format(attempt_id),
            json={"exercise_id": choice["id"], "left": "a", "right": "b"},
        )
        assert response.status_code == 409


class TestSeedIdempotence:
    """`--if-empty` is what keeps a free-tier cold start from wiping progress."""

    def test_is_seeded_is_false_on_an_empty_database(self, db: Session) -> None:
        from app.seed.seed_data import is_seeded

        assert is_seeded(db) is False

    def test_is_seeded_is_true_once_a_course_exists(self, db: Session, course: Course) -> None:
        from app.seed.seed_data import is_seeded

        assert is_seeded(db) is True

    def test_reseeding_converges_rather_than_duplicating(self, db: Session) -> None:
        """The default path is safe to re-run: content is upserted, not appended."""
        from sqlalchemy import func

        from app.models.lesson import Exercise
        from app.seed.seed_data import seed

        seed(db)
        first = (
            db.scalar(select(func.count(Unit.id))),
            db.scalar(select(func.count(Skill.id))),
            db.scalar(select(func.count(Lesson.id))),
            db.scalar(select(func.count(Exercise.id))),
            db.scalar(select(func.count(User.id))),
        )
        seed(db)
        second = (
            db.scalar(select(func.count(Unit.id))),
            db.scalar(select(func.count(Skill.id))),
            db.scalar(select(func.count(Lesson.id))),
            db.scalar(select(func.count(Exercise.id))),
            db.scalar(select(func.count(User.id))),
        )
        assert first == second
