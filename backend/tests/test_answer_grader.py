"""Grading rules for all five exercise types."""

import pytest

from app.models.enums import ExerciseType
from app.services import answer_grader


class TestNormalize:
    """The comparison used by every typed-answer path."""

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("El niño come.", "el nino come"),
            ("  YO   SOY  ", "yo soy"),
            ("¿Cómo estás?", "como estas"),
            ("Buenos días, señor!", "buenos dias senor"),
        ],
    )
    def test_folds_case_accents_and_punctuation(self, raw: str, expected: str) -> None:
        assert answer_grader.normalize(raw) == expected


class TestMultipleChoice:
    def test_accepts_exact_choice(self) -> None:
        assert answer_grader.grade(
            ExerciseType.MULTIPLE_CHOICE, {"choice": "the apple"}, {"choice": "the apple"}
        )

    def test_ignores_case(self) -> None:
        assert answer_grader.grade(
            ExerciseType.MULTIPLE_CHOICE, {"choice": "the apple"}, {"choice": "The Apple"}
        )

    def test_rejects_wrong_choice(self) -> None:
        assert not answer_grader.grade(
            ExerciseType.MULTIPLE_CHOICE, {"choice": "the apple"}, {"choice": "the bread"}
        )

    def test_rejects_malformed_submission(self) -> None:
        assert not answer_grader.grade(
            ExerciseType.MULTIPLE_CHOICE, {"choice": "the apple"}, {"choice": None}
        )


class TestFillBlank:
    def test_accepts_correct_filler_without_accent(self) -> None:
        assert answer_grader.grade(
            ExerciseType.FILL_BLANK, {"choice": "niño"}, {"choice": "nino"}
        )

    def test_rejects_other_option(self) -> None:
        assert not answer_grader.grade(
            ExerciseType.FILL_BLANK, {"choice": "niño"}, {"choice": "niña"}
        )


class TestTranslateWordBank:
    ANSWER = {"words": ["Yo", "soy", "un", "hombre"], "accepted": ["Yo soy un hombre"]}

    def test_accepts_correct_order(self) -> None:
        assert answer_grader.grade(
            ExerciseType.TRANSLATE_WORD_BANK, self.ANSWER, {"words": ["yo", "soy", "un", "hombre"]}
        )

    def test_rejects_scrambled_order(self) -> None:
        assert not answer_grader.grade(
            ExerciseType.TRANSLATE_WORD_BANK, self.ANSWER, {"words": ["soy", "yo", "un", "hombre"]}
        )

    def test_rejects_missing_word(self) -> None:
        assert not answer_grader.grade(
            ExerciseType.TRANSLATE_WORD_BANK, self.ANSWER, {"words": ["yo", "soy", "hombre"]}
        )

    def test_falls_back_to_canonical_words_without_accepted_list(self) -> None:
        assert answer_grader.grade(
            ExerciseType.TRANSLATE_WORD_BANK,
            {"words": ["Ella", "come", "pan"]},
            {"words": ["ella", "come", "pan"]},
        )


class TestTypeAnswer:
    ANSWER = {"accepted": ["Yo soy un hombre.", "Yo soy un hombre"]}

    def test_accepts_exact_sentence(self) -> None:
        assert answer_grader.grade(
            ExerciseType.TYPE_ANSWER, self.ANSWER, {"text": "Yo soy un hombre."}
        )

    def test_ignores_case_accents_and_punctuation(self) -> None:
        assert answer_grader.grade(
            ExerciseType.TYPE_ANSWER,
            {"accepted": ["El niño come pan."]},
            {"text": "  el nino come pan  "},
        )

    def test_rejects_different_sentence(self) -> None:
        assert not answer_grader.grade(
            ExerciseType.TYPE_ANSWER, self.ANSWER, {"text": "Yo soy una mujer"}
        )


class TestMatchPairs:
    ANSWER = {"pairs": {"el gato": "the cat", "el pan": "the bread", "el agua": "the water"}}

    def test_accepts_all_pairs_in_any_order(self) -> None:
        assert answer_grader.grade(
            ExerciseType.MATCH_PAIRS,
            self.ANSWER,
            {
                "pairs": [
                    {"left": "el pan", "right": "the bread"},
                    {"left": "el agua", "right": "the water"},
                    {"left": "el gato", "right": "the cat"},
                ]
            },
        )

    def test_rejects_one_wrong_link(self) -> None:
        assert not answer_grader.grade(
            ExerciseType.MATCH_PAIRS,
            self.ANSWER,
            {
                "pairs": [
                    {"left": "el pan", "right": "the water"},
                    {"left": "el agua", "right": "the bread"},
                    {"left": "el gato", "right": "the cat"},
                ]
            },
        )

    def test_rejects_incomplete_board(self) -> None:
        assert not answer_grader.grade(
            ExerciseType.MATCH_PAIRS,
            self.ANSWER,
            {"pairs": [{"left": "el gato", "right": "the cat"}]},
        )

    def test_rejects_duplicate_left_tile(self) -> None:
        assert not answer_grader.grade(
            ExerciseType.MATCH_PAIRS,
            self.ANSWER,
            {
                "pairs": [
                    {"left": "el gato", "right": "the cat"},
                    {"left": "el gato", "right": "the cat"},
                    {"left": "el gato", "right": "the cat"},
                ]
            },
        )


class TestFormatCorrectAnswer:
    """The one line shown in the red feedback bar."""

    @pytest.mark.parametrize(
        ("exercise_type", "answer", "expected"),
        [
            (ExerciseType.MULTIPLE_CHOICE, {"choice": "the cat"}, "the cat"),
            (ExerciseType.FILL_BLANK, {"choice": "come"}, "come"),
            (
                ExerciseType.TRANSLATE_WORD_BANK,
                {"words": ["Yo", "soy"], "accepted": ["Yo soy"]},
                "Yo soy",
            ),
            (ExerciseType.TYPE_ANSWER, {"accepted": ["Ella come pan."]}, "Ella come pan."),
            (ExerciseType.MATCH_PAIRS, {"pairs": {"el sol": "the sun"}}, "el sol = the sun"),
        ],
    )
    def test_renders_each_type(self, exercise_type, answer, expected) -> None:
        assert answer_grader.format_correct_answer(exercise_type, answer) == expected


def test_every_exercise_type_has_a_grader() -> None:
    """A new enum member must not silently fall through to "incorrect"."""
    for exercise_type in ExerciseType:
        assert exercise_type in answer_grader._GRADERS
