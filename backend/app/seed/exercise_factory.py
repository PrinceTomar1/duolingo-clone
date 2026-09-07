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
from typing import Any

from app.models.enums import ExerciseType
from app.seed.content import SentencePair, SkillContent, WordPair

# Function words make poor fill-in-the-blank targets -- blanking "el" tests
# nothing, so the blank generator skips them.
_STOP_WORDS = {
    "el", "la", "los", "las", "un", "una", "unos", "unas", "y", "o", "de", "en",
    "a", "al", "del", "es", "son", "mi", "su", "con", "que", "hay",
}

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


def _bare(word_pair: WordPair) -> tuple[str, str]:
    """Return the vocabulary pair with leading articles removed.

    Multiple-choice options read better as "apple / bread / water" than as
    "the apple / the bread / the water".
    """
    es = word_pair.es
    en = word_pair.en.removeprefix("the ").removeprefix("to ")
    for article in ("el ", "la ", "los ", "las "):
        if es.startswith(article):
            es = es[len(article):]
            break
    return es, en


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
    rng: random.Random, skill: SkillContent, word_pair: WordPair, ask_in_spanish: bool
) -> dict[str, Any]:
    """Build a four-option translation question.

    ``ask_in_spanish`` flips the direction so a lesson drills both recognition
    (Spanish -> English) and recall (English -> Spanish).
    """
    es, en = _bare(word_pair)
    question, answer = (es, en) if ask_in_spanish else (en, es)
    pool = [_bare(other)[1 if ask_in_spanish else 0] for other in skill.vocabulary]
    options = [answer, *_distractors(rng, pool, answer, 3)]
    rng.shuffle(options)
    return {
        "type": ExerciseType.MULTIPLE_CHOICE,
        "prompt": "Which one of these is “{}”?".format(question),
        "payload": {"question": question, "options": options},
        "correct_answer": {"choice": answer},
        "explanation": "“{}” means “{}”.".format(es, en),
    }


def _match_pairs(rng: random.Random, skill: SkillContent, offset: int) -> dict[str, Any]:
    """Build a five-pair tap-to-match exercise.

    Both columns are shuffled independently so the rows never line up by luck.
    """
    rotated = skill.vocabulary[offset:] + skill.vocabulary[:offset]
    chosen = rotated[:5]
    left = [pair.es for pair in chosen]
    right = [pair.en for pair in chosen]
    rng.shuffle(left)
    rng.shuffle(right)
    return {
        "type": ExerciseType.MATCH_PAIRS,
        "prompt": "Tap the matching pairs",
        "payload": {"left": left, "right": right},
        "correct_answer": {"pairs": {pair.es: pair.en for pair in chosen}},
        "explanation": None,
    }


def _translate_word_bank(
    rng: random.Random, skill: SkillContent, sentence: SentencePair
) -> dict[str, Any]:
    """Build a tap-the-words translation into Spanish."""
    answer_tokens = tokenize(sentence.es)
    answered = {_fold(token) for token in answer_tokens}
    # Distractors must not repeat a word that is already part of the answer,
    # otherwise the bank shows the same tile twice and the puzzle reads as broken.
    other_tokens = [
        token
        for other in skill.sentences
        if other.es != sentence.es
        for token in tokenize(other.es)
        if _fold(token) not in answered
    ]
    bank = answer_tokens + _distractors(rng, other_tokens, "", 3)
    rng.shuffle(bank)
    return {
        "type": ExerciseType.TRANSLATE_WORD_BANK,
        "prompt": "Write this in Spanish",
        "payload": {"source_sentence": sentence.en, "word_bank": bank},
        "correct_answer": {"words": answer_tokens, "accepted": [" ".join(answer_tokens)]},
        "explanation": "“{}” is “{}”.".format(sentence.en, sentence.es),
    }


def _fill_blank(
    rng: random.Random, skill: SkillContent, sentence: SentencePair
) -> dict[str, Any] | None:
    """Blank out one content word and offer three options.

    Returns ``None`` when the sentence is all function words, letting the caller
    fall back to another exercise type rather than emitting a trivial question.
    """
    tokens = tokenize(sentence.es)
    targets = [token for token in tokens if _fold(token) not in _STOP_WORDS and len(token) > 2]
    if not targets:
        return None
    answer = rng.choice(targets)
    blanked = " ".join("___" if token == answer else token for token in tokens)
    pool = [
        token
        for other in skill.sentences
        for token in tokenize(other.es)
        if _fold(token) not in _STOP_WORDS and len(token) > 2
    ]
    options = [answer, *_distractors(rng, pool, answer, 2)]
    rng.shuffle(options)
    return {
        "type": ExerciseType.FILL_BLANK,
        "prompt": "Complete the sentence",
        "payload": {
            "sentence": blanked,
            "options": options,
            "translation": sentence.en,
        },
        "correct_answer": {"choice": answer},
        "explanation": "The full sentence is “{}”.".format(sentence.es),
    }


def _type_answer(sentence: SentencePair) -> dict[str, Any]:
    """Build a free-typing translation.

    ``accepted`` carries the punctuation-free variant too; the grader also folds
    case and accents, so a learner without a Spanish keyboard is not punished.
    """
    return {
        "type": ExerciseType.TYPE_ANSWER,
        "prompt": "Write this in Spanish",
        "payload": {"source_sentence": sentence.en},
        "correct_answer": {"accepted": [sentence.es, strip_punctuation(sentence.es)]},
        "explanation": "“{}” is “{}”.".format(sentence.en, sentence.es),
    }


def build_lesson_exercises(skill: SkillContent, lesson_index: int) -> list[dict[str, Any]]:
    """Generate one lesson's worth of exercises for a skill.

    ``lesson_index`` rotates which vocabulary and sentences are drawn, so the
    lessons inside a skill drill different material rather than repeating.
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
            built = _multiple_choice(rng, skill, word_pair, ask_in_spanish=vocab_cursor % 2 == 0)
            vocab_cursor += 1
        elif exercise_type is ExerciseType.MATCH_PAIRS:
            built = _match_pairs(rng, skill, vocab_offset)
        elif exercise_type is ExerciseType.TRANSLATE_WORD_BANK:
            built = _translate_word_bank(rng, skill, sentences[sentence_cursor % len(sentences)])
            sentence_cursor += 1
        elif exercise_type is ExerciseType.FILL_BLANK:
            sentence = sentences[sentence_cursor % len(sentences)]
            sentence_cursor += 1
            built = _fill_blank(rng, skill, sentence) or _type_answer(sentence)
        else:
            built = _type_answer(sentences[sentence_cursor % len(sentences)])
            sentence_cursor += 1
        exercises.append({**built, "order_index": len(exercises)})

    return exercises
