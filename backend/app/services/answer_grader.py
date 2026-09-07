"""Server-side grading for the five exercise types.

Every function here is pure: it takes the stored ``correct_answer`` and the
learner's submission and returns a boolean. No database, no clock, no request
context -- which is what makes the whole module directly unit-testable and
lets the router layer stay a thin adapter.

Grading lives on the server because the client is not trustworthy. If the
browser knew the right answer it could award itself XP; instead the answer key
never leaves this process and the client only ever learns the verdict.
"""

import unicodedata
from typing import Any, Callable

from app.models.enums import ExerciseType


def normalize(text: str) -> str:
    """Fold a learner's typing down to what actually matters.

    Case, accents, punctuation and repeated whitespace are all stripped, so
    ``"El nino, come."`` matches ``"el niño come"``. Accents in particular are
    folded because most learners type on a keyboard that cannot produce them,
    and refusing the answer would teach nothing about the language.
    """
    decomposed = unicodedata.normalize("NFD", text.strip().lower())
    without_accents = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    kept = "".join(ch if ch.isalnum() or ch.isspace() else " " for ch in without_accents)
    return " ".join(kept.split())


def _matches_any(candidate: str, accepted: Any) -> bool:
    """True when ``candidate`` normalizes equal to any accepted spelling."""
    if not isinstance(accepted, list):
        return False
    target = normalize(candidate)
    return any(isinstance(option, str) and normalize(option) == target for option in accepted)


def grade_multiple_choice(correct_answer: dict[str, Any], submitted: dict[str, Any]) -> bool:
    """One option out of four; compared normalized so casing never fails a learner."""
    choice = submitted.get("choice")
    expected = correct_answer.get("choice")
    if not isinstance(choice, str) or not isinstance(expected, str):
        return False
    return normalize(choice) == normalize(expected)


def grade_fill_blank(correct_answer: dict[str, Any], submitted: dict[str, Any]) -> bool:
    """Same shape as multiple choice -- one token chosen to fill a gap.

    Kept as its own function rather than aliased so the two can diverge (free
    typing into the blank, multiple accepted fillers) without touching callers.
    """
    choice = submitted.get("choice")
    expected = correct_answer.get("choice")
    if not isinstance(choice, str) or not isinstance(expected, str):
        return False
    return normalize(choice) == normalize(expected)


def grade_translate_word_bank(correct_answer: dict[str, Any], submitted: dict[str, Any]) -> bool:
    """Tapped tiles, joined into a sentence and compared against the accepted forms.

    Order matters -- that is the whole exercise -- but spacing and capitalisation
    do not.
    """
    words = submitted.get("words")
    if not isinstance(words, list) or not all(isinstance(word, str) for word in words):
        return False
    sentence = " ".join(words)
    accepted = correct_answer.get("accepted")
    if _matches_any(sentence, accepted):
        return True
    # Fall back to the canonical token list when no ``accepted`` list was stored.
    expected_words = correct_answer.get("words")
    if isinstance(expected_words, list):
        return normalize(sentence) == normalize(" ".join(str(word) for word in expected_words))
    return False


def grade_type_answer(correct_answer: dict[str, Any], submitted: dict[str, Any]) -> bool:
    """Free typing, matched against every accepted spelling of the sentence."""
    text = submitted.get("text")
    if not isinstance(text, str):
        return False
    return _matches_any(text, correct_answer.get("accepted"))


def grade_match_pairs(correct_answer: dict[str, Any], submitted: dict[str, Any]) -> bool:
    """Every pair must be linked, and every link must be right.

    A partially-matched board is not a correct answer, so the submitted pair
    count has to equal the stored one.
    """
    pairs = submitted.get("pairs")
    expected = correct_answer.get("pairs")
    if not isinstance(pairs, list) or not isinstance(expected, dict):
        return False
    if len(pairs) != len(expected):
        return False
    expected_normalized = {normalize(str(k)): normalize(str(v)) for k, v in expected.items()}
    seen: set[str] = set()
    for pair in pairs:
        if not isinstance(pair, dict):
            return False
        left, right = pair.get("left"), pair.get("right")
        if not isinstance(left, str) or not isinstance(right, str):
            return False
        key = normalize(left)
        if key in seen or expected_normalized.get(key) != normalize(right):
            return False
        seen.add(key)
    return True


# Dispatch table rather than an if/elif chain: adding a sixth exercise type is a
# single entry here plus one pure function, and the router never changes.
_GRADERS: dict[ExerciseType, Callable[[dict[str, Any], dict[str, Any]], bool]] = {
    ExerciseType.MULTIPLE_CHOICE: grade_multiple_choice,
    ExerciseType.FILL_BLANK: grade_fill_blank,
    ExerciseType.TRANSLATE_WORD_BANK: grade_translate_word_bank,
    ExerciseType.TYPE_ANSWER: grade_type_answer,
    ExerciseType.MATCH_PAIRS: grade_match_pairs,
}


def grade(
    exercise_type: ExerciseType,
    correct_answer: dict[str, Any],
    submitted: dict[str, Any],
) -> bool:
    """Grade a submission of any type.

    Raises ``KeyError`` for an unknown type rather than silently returning
    ``False``, so a content bug surfaces as a 500 instead of an unfair mark.
    """
    return _GRADERS[exercise_type](correct_answer, submitted)


def format_correct_answer(exercise_type: ExerciseType, correct_answer: dict[str, Any]) -> str:
    """Render the answer key as the one line the red feedback bar shows.

    Only ever called *after* grading, and only for the exercise just answered,
    so revealing it here does not leak the rest of the lesson.
    """
    if exercise_type in (ExerciseType.MULTIPLE_CHOICE, ExerciseType.FILL_BLANK):
        return str(correct_answer.get("choice", ""))
    if exercise_type is ExerciseType.TRANSLATE_WORD_BANK:
        accepted = correct_answer.get("accepted")
        if isinstance(accepted, list) and accepted:
            return str(accepted[0])
        words = correct_answer.get("words", [])
        return " ".join(str(word) for word in words) if isinstance(words, list) else ""
    if exercise_type is ExerciseType.TYPE_ANSWER:
        accepted = correct_answer.get("accepted", [])
        return str(accepted[0]) if isinstance(accepted, list) and accepted else ""
    pairs = correct_answer.get("pairs", {})
    if isinstance(pairs, dict):
        return ", ".join("{} = {}".format(k, v) for k, v in pairs.items())
    return ""
