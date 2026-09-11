"""Turns declarative skill content into concrete exercise rows.

Every generator here is deterministic: it seeds its own ``Random`` from the
skill title and lesson index, so re-running the seed script produces byte-identical
exercises and the idempotent upsert has nothing to change.

Each function returns a plain dict matching the ``exercises`` table columns. The
``payload`` half is what the client renders; the ``correct_answer`` half never
leaves the server.
"""

import random
import unicodedata
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from app.models.enums import ExerciseType

if TYPE_CHECKING:  # pragma: no cover - avoids a circular import at runtime
    from app.seed.content import SentencePair, SkillContent, WordPair


@dataclass(frozen=True)
class LanguageProfile:
    """The language-specific facts this module needs, so it drills no
    particular language by default.

    Everything here used to be hardcoded to Spanish (prompts literally said
    "in Spanish", the stop-word list was Spanish function words, the article
    list was "el/la/los/las"). Adding a second course meant pulling those out
    into data owned by ``content.py``, one profile per course, rather than
    duplicating this whole module per language.
    """

    name: str
    # Function words make poor fill-in-the-blank targets -- blanking "el"
    # tests nothing, so the blank generator skips them.
    stop_words: frozenset[str]
    # Leading articles stripped from multiple-choice options: "the apple" is
    # awkward next to "bread" and "water", so is "el/la/le/la" next to their
    # target-language equivalents.
    articles: tuple[str, ...]


# The five-type running order used by every lesson. Fixed rather than random so
# a learner always meets a recognition exercise before a production one.
_LESSON_SHAPE: list[ExerciseType] = [
    ExerciseType.MULTIPLE_CHOICE,
    ExerciseType.MATCH_PAIRS,
    ExerciseType.MULTIPLE_CHOICE,
    ExerciseType.TRANSLATE_WORD_BANK,
    ExerciseType.FILL_BLANK,
    ExerciseType.MULTIPLE_CHOICE,
    ExerciseType.TRANSLATE_WORD_BANK,
    ExerciseType.FILL_BLANK,
    ExerciseType.TYPE_ANSWER,
]


def strip_punctuation(text: str) -> str:
    """Drop the punctuation that word banks and typed answers should ignore."""
    return "".join(ch for ch in text if ch.isalnum() or ch.isspace() or ch == "'").strip()


def tokenize(sentence: str) -> list[str]:
    """Split a sentence into the tiles a word bank shows."""
    return strip_punctuation(sentence).split()


def _fold(text: str) -> str:
    """Lowercase and strip accents -- used only to compare, never to display."""
    decomposed = unicodedata.normalize("NFD", text.lower())
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


def _bare(word_pair: "WordPair", profile: LanguageProfile) -> tuple[str, str]:
    """Return the vocabulary pair with leading articles removed.

    Multiple-choice options read better as "apple / bread / water" than as
    "the apple / the bread / the water".
    """
    target = word_pair.target
    english = word_pair.english.removeprefix("the ").removeprefix("to ")
    for article in profile.articles:
        if target.startswith(article):
            target = target[len(article):]
            break
    return target, english


def _distractors(rng: random.Random, pool: list[str], correct: str, count: int) -> list[str]:
    """Pick ``count`` wrong options that are not the right answer or duplicates."""
    candidates = [item for item in pool if _fold(item) != _fold(correct)]
    unique: list[str] = []
    for item in candidates:
        if all(_fold(item) != _fold(seen) for seen in unique):
            unique.append(item)
    rng.shuffle(unique)
    return unique[:count]


def _multiple_choice(
    rng: random.Random,
    skill: "SkillContent",
    word_pair: "WordPair",
    ask_in_target: bool,
    profile: LanguageProfile,
) -> dict[str, Any]:
    """Build a four-option translation question.

    ``ask_in_target`` flips the direction so a lesson drills both recognition
    (target language -> English) and recall (English -> target language).
    """
    target, english = _bare(word_pair, profile)
    question, answer = (target, english) if ask_in_target else (english, target)
    pool = [_bare(other, profile)[1 if ask_in_target else 0] for other in skill.vocabulary]
    options = [answer, *_distractors(rng, pool, answer, 3)]
    rng.shuffle(options)
    return {
        "type": ExerciseType.MULTIPLE_CHOICE,
        "prompt": "Which one of these is “{}”?".format(question),
        "payload": {"question": question, "options": options},
        "correct_answer": {"choice": answer},
        "explanation": "“{}” means “{}”.".format(target, english),
    }


def _match_pairs(rng: random.Random, skill: "SkillContent", offset: int) -> dict[str, Any]:
    """Build a five-pair tap-to-match exercise.

    Both columns are shuffled independently so the rows never line up by luck.
    """
    rotated = skill.vocabulary[offset:] + skill.vocabulary[:offset]
    chosen = rotated[:5]
    left = [pair.target for pair in chosen]
    right = [pair.english for pair in chosen]
    rng.shuffle(left)
    rng.shuffle(right)
    return {
        "type": ExerciseType.MATCH_PAIRS,
        "prompt": "Tap the matching pairs",
        "payload": {"left": left, "right": right},
        "correct_answer": {"pairs": {pair.target: pair.english for pair in chosen}},
        "explanation": None,
    }


def _translate_word_bank(
    rng: random.Random, skill: "SkillContent", sentence: "SentencePair", profile: LanguageProfile
) -> dict[str, Any]:
    """Build a tap-the-words translation into the target language."""
    answer_tokens = tokenize(sentence.target)
    answered = {_fold(token) for token in answer_tokens}
    # Distractors must not repeat a word that is already part of the answer,
    # otherwise the bank shows the same tile twice and the puzzle reads as broken.
    other_tokens = [
        token
        for other in skill.sentences
        if other.target != sentence.target
        for token in tokenize(other.target)
        if _fold(token) not in answered
    ]
    bank = answer_tokens + _distractors(rng, other_tokens, "", 3)
    rng.shuffle(bank)
    return {
        "type": ExerciseType.TRANSLATE_WORD_BANK,
        "prompt": "Write this in {}".format(profile.name),
        "payload": {"source_sentence": sentence.english, "word_bank": bank},
        "correct_answer": {"words": answer_tokens, "accepted": [" ".join(answer_tokens)]},
        "explanation": "“{}” is “{}”.".format(sentence.english, sentence.target),
    }


def _fill_blank(
    rng: random.Random, skill: "SkillContent", sentence: "SentencePair", profile: LanguageProfile
) -> dict[str, Any] | None:
    """Blank out one content word and offer three options.

    Returns ``None`` when the sentence is all function words, letting the caller
    fall back to another exercise type rather than emitting a trivial question.
    """
    tokens = tokenize(sentence.target)
    targets = [
        token for token in tokens if _fold(token) not in profile.stop_words and len(token) > 2
    ]
    if not targets:
        return None
    answer = rng.choice(targets)
    blanked = " ".join("___" if token == answer else token for token in tokens)
    pool = [
        token
        for other in skill.sentences
        for token in tokenize(other.target)
        if _fold(token) not in profile.stop_words and len(token) > 2
    ]
    options = [answer, *_distractors(rng, pool, answer, 2)]
    rng.shuffle(options)
    return {
        "type": ExerciseType.FILL_BLANK,
        "prompt": "Complete the sentence",
        "payload": {
            "sentence": blanked,
            "options": options,
            "translation": sentence.english,
        },
        "correct_answer": {"choice": answer},
        "explanation": "The full sentence is “{}”.".format(sentence.target),
    }


def _type_answer(sentence: "SentencePair", profile: LanguageProfile) -> dict[str, Any]:
    """Build a free-typing translation.

    ``accepted`` carries the punctuation-free variant too; the grader also folds
    case and accents, so a learner without the target language's keyboard layout
    is not punished.
    """
    return {
        "type": ExerciseType.TYPE_ANSWER,
        "prompt": "Write this in {}".format(profile.name),
        "payload": {"source_sentence": sentence.english},
        "correct_answer": {"accepted": [sentence.target, strip_punctuation(sentence.target)]},
        "explanation": "“{}” is “{}”.".format(sentence.english, sentence.target),
    }


def build_lesson_exercises(
    skill: "SkillContent", lesson_index: int, profile: LanguageProfile
) -> list[dict[str, Any]]:
    """Generate one lesson's worth of exercises for a skill.

    ``lesson_index`` rotates which vocabulary and sentences are drawn, so the
    lessons inside a skill drill different material rather than repeating.
    ``profile`` is the calling course's language facts -- see ``LanguageProfile``.
    """
    rng = random.Random("{}::{}".format(skill.title, lesson_index))
    vocab_offset = lesson_index * 3
    sentence_offset = lesson_index * 2

    vocabulary = skill.vocabulary[vocab_offset:] + skill.vocabulary[:vocab_offset]
    sentences = skill.sentences[sentence_offset:] + skill.sentences[:sentence_offset]

    exercises: list[dict[str, Any]] = []
    vocab_cursor = 0
    sentence_cursor = 0

    for exercise_type in _LESSON_SHAPE:
        if exercise_type is ExerciseType.MULTIPLE_CHOICE:
            word_pair = vocabulary[vocab_cursor % len(vocabulary)]
            built = _multiple_choice(
                rng, skill, word_pair, ask_in_target=vocab_cursor % 2 == 0, profile=profile
            )
            vocab_cursor += 1
        elif exercise_type is ExerciseType.MATCH_PAIRS:
            built = _match_pairs(rng, skill, vocab_offset)
        elif exercise_type is ExerciseType.TRANSLATE_WORD_BANK:
            built = _translate_word_bank(
                rng, skill, sentences[sentence_cursor % len(sentences)], profile
            )
            sentence_cursor += 1
        elif exercise_type is ExerciseType.FILL_BLANK:
            sentence = sentences[sentence_cursor % len(sentences)]
            sentence_cursor += 1
            built = _fill_blank(rng, skill, sentence, profile) or _type_answer(sentence, profile)
        else:
            built = _type_answer(sentences[sentence_cursor % len(sentences)], profile)
            sentence_cursor += 1
        exercises.append({**built, "order_index": len(exercises)})

    return exercises
