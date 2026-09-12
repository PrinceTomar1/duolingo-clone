"""Shared pytest fixtures.

Every test runs against a fresh in-memory SQLite database, so the suite never
touches the developer's ``duolingo.db`` and tests cannot leak state into each
other. ``StaticPool`` keeps one connection alive for the whole test, which is
what makes ``:memory:`` usable across the several sessions a request would open.
"""

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core import clock, rate_limit
from app.core.database import Base
from app.models.achievement import Achievement
from app.models.course import Course, Skill, Unit
from app.models.lesson import Exercise, Lesson
from app.models.stats import UserStats
from app.models.user import User
from app.seed import content
from app.seed.exercise_factory import build_lesson_exercises


@pytest.fixture(autouse=True)
def real_time() -> None:
    """Reset the simulated clock around every test.

    The clock offset is process-global, so a test that advances the day must not
    be able to poison the next one.
    """
    clock.reset()
    yield
    clock.reset()


@pytest.fixture(autouse=True)
def no_rate_limit_history() -> None:
    """Reset the login rate limiter around every test.

    It is process-global by design (see its module docstring), so a test that
    trips it must not leave the next test's identical username locked out.
    """
    rate_limit.reset_all()
    yield
    rate_limit.reset_all()


@pytest.fixture
def db() -> Session:
    """A session bound to a throwaway in-memory database."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _fk_on(dbapi_connection, _record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = factory()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def course(db: Session) -> Course:
    """A two-unit slice of the real course content.

    Uses the same content module and exercise factory as production seeding, so
    the tests exercise real exercise payloads rather than invented fixtures.
    """
    course = Course(from_language="English", to_language="Spanish", title="Spanish")
    db.add(course)
    db.flush()

    for unit_index, unit_spec in enumerate(content.SPANISH_UNITS[:2]):
        unit = Unit(
            course_id=course.id,
            order_index=unit_index,
            title=unit_spec.title,
            description=unit_spec.description,
            color_hex=unit_spec.color_hex,
        )
        db.add(unit)
        db.flush()
        for skill_index, skill_spec in enumerate(unit_spec.skills):
            skill = Skill(
                unit_id=unit.id,
                order_index=skill_index,
                title=skill_spec.title,
                icon=skill_spec.icon,
                required_crowns_to_unlock=skill_spec.required_crowns_to_unlock,
            )
            db.add(skill)
            db.flush()
            for lesson_index in range(skill_spec.lesson_count):
                lesson = Lesson(skill_id=skill.id, order_index=lesson_index, xp_reward=10)
                db.add(lesson)
                db.flush()
                for spec in build_lesson_exercises(skill_spec, lesson_index, content.SPANISH_PROFILE):
                    db.add(
                        Exercise(
                            lesson_id=lesson.id,
                            order_index=spec["order_index"],
                            type=spec["type"],
                            prompt=spec["prompt"],
                            payload=spec["payload"],
                            correct_answer=spec["correct_answer"],
                            explanation=spec["explanation"],
                        )
                    )
    for spec in content.ACHIEVEMENTS:
        db.add(
            Achievement(
                code=str(spec["code"]),
                title=str(spec["title"]),
                description=str(spec["description"]),
                icon=str(spec["icon"]),
                color_hex=str(spec["color_hex"]),
                metric=str(spec["metric"]),
                target=int(spec["target"]),
            )
        )
    db.commit()
    return course


@pytest.fixture
def user(db: Session) -> User:
    """A learner with a full heart bar and no history."""
    learner = User(username="tester", display_name="Tester", avatar_color="#58CC02")
    db.add(learner)
    db.flush()
    db.add(
        UserStats(
            user_id=learner.id,
            total_xp=0,
            current_streak=0,
            longest_streak=0,
            hearts=5,
            # Anchored to the simulated "now" so a test that empties the heart
            # bar is not silently topped back up by lazy regeneration.
            hearts_updated_at=clock.now(),
            gems=500,
            daily_goal_xp=20,
        )
    )
    db.commit()
    return learner


@pytest.fixture
def other_user(db: Session) -> User:
    """A second, independent learner -- for tests asserting one learner's
    actions (notably the per-learner demo clock) do not leak onto another's."""
    learner = User(username="tester2", display_name="Tester Two", avatar_color="#1CB0F6")
    db.add(learner)
    db.flush()
    db.add(
        UserStats(
            user_id=learner.id,
            total_xp=0,
            current_streak=0,
            longest_streak=0,
            hearts=5,
            hearts_updated_at=clock.now(),
            gems=500,
            daily_goal_xp=20,
        )
    )
    db.commit()
    return learner
