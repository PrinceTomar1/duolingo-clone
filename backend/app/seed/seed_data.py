"""Populate the database so the app is usable the moment it is cloned.

Run with ``python -m app.seed.seed_data``.

Idempotent by convergence: course content is upserted on its natural keys
(order within a parent), and each demo learner's *derived* rows -- progress,
attempts, ledger, achievements -- are rebuilt from scratch. Running the script
twice leaves the database in exactly the state running it once does.
"""

import sys
from datetime import date, timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core import clock
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.achievement import Achievement, UserAchievement
from app.models.course import Course, Skill, Unit
from app.models.lesson import Exercise, Lesson
from app.models.progress import LessonAttempt, UserProgress
from app.models.stats import DailyXp, UserStats
from app.models.user import User
from app.seed import content
from app.seed.exercise_factory import build_lesson_exercises
from app.services import gamification_service, path_service
from app.services.achievement_service import sync_achievements

DEMO_USERNAME = "prince"
DEMO_TOTAL_XP = 1240
DEMO_GEMS = 500

# Two blocks of activity separated by a two-day gap. The recent block is exactly
# seven days long and reaches today, so the derived streak is 7 -- and the gap
# proves the streak really is derived rather than an ever-growing counter.
_RECENT_DAILY_XP = [55, 70, 40, 90, 35, 60, 30]
_OLDER_DAILY_XP = [100, 85, 120, 95, 110, 130, 90]

# username, display name, avatar colour, weekly XP, all-time XP
_RIVALS = [
    ("sofia", "Sofía Márquez", "#CE82FF", 620, 4310),
    ("kenji", "Kenji Watanabe", "#1CB0F6", 545, 3980),
    ("amara", "Amara Okafor", "#FF9600", 470, 2870),
    ("lucas", "Lucas Silva", "#FF4B4B", 410, 2540),
    ("mei", "Mei Chen", "#2B70C9", 355, 1990),
    ("diego", "Diego Herrera", "#58CC02", 300, 1720),
    ("nadia", "Nadia Farouk", "#FFC800", 245, 1180),
    ("tom", "Tom Becker", "#777777", 190, 860),
    ("priya", "Priya Nair", "#89E219", 120, 540),
]


def _upsert_course(db: Session) -> Course:
    """Create or update the single course row."""
    course = db.scalar(
        select(Course).where(
            Course.from_language == content.COURSE_FROM_LANGUAGE,
            Course.to_language == content.COURSE_TO_LANGUAGE,
        )
    )
    if course is None:
        course = Course(
            from_language=content.COURSE_FROM_LANGUAGE,
            to_language=content.COURSE_TO_LANGUAGE,
            title=content.COURSE_TITLE,
        )
        db.add(course)
        db.flush()
    course.title = content.COURSE_TITLE
    return course


def _upsert_exercises(db: Session, lesson: Lesson, skill: content.SkillContent, index: int) -> None:
    """Regenerate a lesson's exercises, matching existing rows by position."""
    existing = {row.order_index: row for row in lesson.exercises}
    for spec in build_lesson_exercises(skill, index):
        row = existing.pop(spec["order_index"], None)
        if row is None:
            row = Exercise(lesson_id=lesson.id, order_index=spec["order_index"])
            db.add(row)
        row.type = spec["type"]
        row.prompt = spec["prompt"]
        row.payload = spec["payload"]
        row.correct_answer = spec["correct_answer"]
        row.explanation = spec["explanation"]
        row.audio_url = None
    # Anything left over came from an older, longer version of the lesson.
    for stale in existing.values():
        db.delete(stale)


def _upsert_content(db: Session, course: Course) -> None:
    """Write the full unit -> skill -> lesson -> exercise tree."""
    for unit_index, unit_spec in enumerate(content.UNITS):
        unit = db.scalar(
            select(Unit).where(Unit.course_id == course.id, Unit.order_index == unit_index)
        )
        if unit is None:
            unit = Unit(course_id=course.id, order_index=unit_index)
            db.add(unit)
        unit.title = unit_spec.title
        unit.description = unit_spec.description
        unit.color_hex = unit_spec.color_hex
        db.flush()

        for skill_index, skill_spec in enumerate(unit_spec.skills):
            skill = db.scalar(
                select(Skill).where(Skill.unit_id == unit.id, Skill.order_index == skill_index)
            )
            if skill is None:
                skill = Skill(unit_id=unit.id, order_index=skill_index)
                db.add(skill)
            skill.title = skill_spec.title
            skill.icon = skill_spec.icon
            skill.required_crowns_to_unlock = skill_spec.required_crowns_to_unlock
            db.flush()

            for lesson_index in range(skill_spec.lesson_count):
                lesson = db.scalar(
                    select(Lesson).where(
                        Lesson.skill_id == skill.id, Lesson.order_index == lesson_index
                    )
                )
                if lesson is None:
                    lesson = Lesson(skill_id=skill.id, order_index=lesson_index)
                    db.add(lesson)
                lesson.xp_reward = settings.base_lesson_xp
                db.flush()
                db.refresh(lesson)
                _upsert_exercises(db, lesson, skill_spec, lesson_index)


def _upsert_achievements(db: Session) -> None:
    """Write the badge definitions, keyed on their stable ``code``."""
    for spec in content.ACHIEVEMENTS:
        row = db.scalar(select(Achievement).where(Achievement.code == spec["code"]))
        if row is None:
            row = Achievement(code=str(spec["code"]))
            db.add(row)
        row.title = str(spec["title"])
        row.description = str(spec["description"])
        row.icon = str(spec["icon"])
        row.color_hex = str(spec["color_hex"])
        row.metric = str(spec["metric"])
        row.target = int(spec["target"])  # type: ignore[arg-type]


def _upsert_user(db: Session, username: str, display_name: str, color: str) -> User:
    """Create or update a learner and make sure they have a stats row."""
    user = db.scalar(select(User).where(User.username == username))
    if user is None:
        user = User(username=username)
        db.add(user)
    user.display_name = display_name
    user.avatar_color = color
    # Flush so the autoincrement id exists before it is used as a foreign key.
    db.flush()
    if db.get(UserStats, user.id) is None:
        db.add(UserStats(user_id=user.id, hearts_updated_at=clock.now()))
    db.flush()
    return user


def _reset_learner_state(db: Session, user_id: int) -> None:
    """Clear every derived row so the demo state can be rebuilt deterministically."""
    for model in (UserProgress, LessonAttempt, DailyXp, UserAchievement):
        db.execute(delete(model).where(model.user_id == user_id))
    db.flush()


def _write_ledger(db: Session, user_id: int, values: list[int], start_offset: int, today: date) -> None:
    """Insert one ``daily_xp`` row per value, ending ``start_offset`` days ago."""
    for position, amount in enumerate(values):
        day = today - timedelta(days=start_offset - position)
        db.add(DailyXp(user_id=user_id, date=day, xp_earned=amount))


def _seed_demo_learner(db: Session, course: Course) -> User:
    """Build ``prince``: Unit 1 finished, part-way through Unit 2, 7-day streak."""
    user = _upsert_user(db, DEMO_USERNAME, "Prince Tomar", "#1CB0F6")
    _reset_learner_state(db, user.id)
    today = clock.today()

    # 14 ledger days summing to exactly the advertised total XP. The first day
    # absorbs the rounding so the headline number and the ledger always agree.
    recent = list(_RECENT_DAILY_XP)
    older = list(_OLDER_DAILY_XP)
    older[0] += DEMO_TOTAL_XP - (sum(recent) + sum(older))
    _write_ledger(db, user.id, older, start_offset=15, today=today)
    _write_ledger(db, user.id, recent, start_offset=6, today=today)

    # Lessons finished: every lesson in Unit 1, all of Food, and the first
    # lesson of Family -- i.e. "mid Unit 2" on the path.
    units = db.scalars(
        select(Unit).where(Unit.course_id == course.id).order_by(Unit.order_index)
    ).all()
    completed_lessons: list[Lesson] = []
    for skill in db.scalars(
        select(Skill).where(Skill.unit_id == units[0].id).order_by(Skill.order_index)
    ).all():
        completed_lessons.extend(skill.lessons)
    unit_two_skills = db.scalars(
        select(Skill).where(Skill.unit_id == units[1].id).order_by(Skill.order_index)
    ).all()
    completed_lessons.extend(unit_two_skills[0].lessons)
    completed_lessons.append(unit_two_skills[1].lessons[0])

    # Three flawless runs, which leaves the Sharpshooter badge at 3 of 5.
    perfect_positions = {2, 5, 9}
    # Progress rows are kept in a dict rather than re-queried per lesson: the
    # session has autoflush off, so a pending row would be invisible to a query
    # and the same skill would get a duplicate row.
    progress_by_skill: dict[int, UserProgress] = {}
    for position, lesson in enumerate(completed_lessons):
        hearts_lost = 0 if position in perfect_positions else 1 + position % 2
        finished_at = clock.now() - timedelta(days=max(0, 13 - position), minutes=position * 7)
        db.add(
            LessonAttempt(
                user_id=user.id,
                lesson_id=lesson.id,
                started_at=finished_at - timedelta(minutes=4),
                completed_at=finished_at,
                hearts_lost=hearts_lost,
                exercises_answered=len(lesson.exercises),
                xp_earned=gamification_service.calculate_lesson_xp(
                    lesson.xp_reward, hearts_lost, settings.max_hearts - hearts_lost
                ),
                is_completed=True,
            )
        )
        progress = progress_by_skill.get(lesson.skill_id)
        if progress is None:
            # Zeros are passed explicitly: column defaults only land at flush
            # time, so the attribute would be None for the increment below.
            progress = UserProgress(
                user_id=user.id,
                skill_id=lesson.skill_id,
                crowns=0,
                lessons_completed=0,
                is_unlocked=True,
            )
            db.add(progress)
            progress_by_skill[lesson.skill_id] = progress
        progress.crowns += 1
        progress.lessons_completed += 1
    db.flush()

    stats = db.get(UserStats, user.id)
    assert stats is not None
    stats.total_xp = DEMO_TOTAL_XP
    stats.gems = DEMO_GEMS
    stats.hearts = settings.max_hearts
    stats.hearts_updated_at = clock.now()
    stats.daily_goal_xp = settings.default_daily_goal_xp
    gamification_service.refresh_streak(db, stats, today)
    path_service.sync_unlock_flags(db, course, user.id)
    sync_achievements(db, user.id)
    return user


def _seed_rivals(db: Session, course: Course) -> None:
    """Nine other learners so the leaderboard has a real field."""
    today = clock.today()
    for username, display_name, color, weekly_xp, total_xp in _RIVALS:
        user = _upsert_user(db, username, display_name, color)
        _reset_learner_state(db, user.id)
        # Spread the week's XP across seven days, remainder on the first day.
        per_day = weekly_xp // 7
        values = [per_day] * 7
        values[0] += weekly_xp - sum(values)
        _write_ledger(db, user.id, values, start_offset=6, today=today)

        stats = db.get(UserStats, user.id)
        assert stats is not None
        stats.total_xp = total_xp
        stats.gems = 100 + total_xp // 20
        stats.hearts = settings.max_hearts
        stats.hearts_updated_at = clock.now()
        # Crowns roughly track XP, which keeps each rival's profile self-consistent.
        for skill in db.scalars(select(Skill).order_by(Skill.id).limit(total_xp // 400 + 1)).all():
            db.add(
                UserProgress(
                    user_id=user.id,
                    skill_id=skill.id,
                    crowns=len(skill.lessons),
                    lessons_completed=len(skill.lessons),
                    is_unlocked=True,
                )
            )
        db.flush()
        gamification_service.refresh_streak(db, stats, today)
        path_service.sync_unlock_flags(db, course, user.id)
        sync_achievements(db, user.id)


def seed(db: Session) -> None:
    """Run every seeding step in dependency order."""
    course = _upsert_course(db)
    _upsert_content(db, course)
    _upsert_achievements(db)
    db.flush()
    _seed_demo_learner(db, course)
    _seed_rivals(db, course)
    db.commit()


def is_seeded(db: Session) -> bool:
    """True when a course already exists, i.e. this database has been seeded."""
    return db.scalar(select(Course.id)) is not None


def main() -> None:
    """Entry point for ``python -m app.seed.seed_data``.

    ``--if-empty`` seeds only a database that has no course yet. Deployed
    environments use it in their start command: a free-tier host restarts the
    process whenever it wakes from idle, and an unconditional seed would reset
    every learner's progress on each cold start. Locally the default (no flag)
    still converges the demo learners back to a known state, which is what makes
    re-running it useful during development.
    """
    seed_only_if_empty = "--if-empty" in sys.argv

    with SessionLocal() as db:
        if seed_only_if_empty and is_seeded(db):
            print("Database already seeded; leaving learner progress untouched.")
            return
        seed(db)
        course = db.scalar(select(Course))
        assert course is not None
        lessons = db.scalar(select(Lesson.id))
        print(
            "Seeded {} -> {}: {} units, {} skills, {} lessons, {} exercises, {} users.".format(
                course.from_language,
                course.to_language,
                len(db.scalars(select(Unit.id)).all()),
                len(db.scalars(select(Skill.id)).all()),
                len(db.scalars(select(Lesson.id)).all()),
                len(db.scalars(select(Exercise.id)).all()),
                len(db.scalars(select(User.id)).all()),
            )
        )
        assert lessons is not None


if __name__ == "__main__":
    main()
