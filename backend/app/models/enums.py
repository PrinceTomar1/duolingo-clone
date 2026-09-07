"""Enumerations shared by models and schemas.

Kept in their own module so Pydantic schemas can import them without pulling in
SQLAlchemy, which keeps the schema layer free of ORM imports.
"""

from enum import Enum


class ExerciseType(str, Enum):
    """The five exercise formats the lesson player knows how to render.

    Inherits from ``str`` so it serialises straight to JSON and compares equal
    to its wire value, which keeps the API contract readable.
    """

    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
    TRANSLATE_WORD_BANK = "TRANSLATE_WORD_BANK"
    MATCH_PAIRS = "MATCH_PAIRS"
    FILL_BLANK = "FILL_BLANK"
    TYPE_ANSWER = "TYPE_ANSWER"


class SkillState(str, Enum):
    """Per-user state of a skill node on the learning path.

    Derived server-side from crowns and lesson completion; never stored.
    """

    LOCKED = "locked"
    AVAILABLE = "available"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
