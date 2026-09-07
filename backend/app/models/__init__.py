"""SQLAlchemy models.

Every model is re-exported here so that importing ``app.models`` registers the
full mapper configuration -- Alembic's autogenerate and ``Base.metadata`` both
depend on all classes having been imported exactly once.
"""

from app.models.achievement import Achievement, UserAchievement
from app.models.course import Course, Skill, Unit
from app.models.enums import ExerciseType, SkillState
from app.models.lesson import Exercise, Lesson
from app.models.progress import LessonAttempt, UserProgress
from app.models.stats import DailyXp, UserStats
from app.models.user import User

__all__ = [
    "Achievement",
    "Course",
    "DailyXp",
    "Exercise",
    "ExerciseType",
    "Lesson",
    "LessonAttempt",
    "Skill",
    "SkillState",
    "Unit",
    "User",
    "UserAchievement",
    "UserProgress",
    "UserStats",
]
