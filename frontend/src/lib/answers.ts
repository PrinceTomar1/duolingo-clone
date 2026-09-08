/**
 * Turns the player's in-progress draft into the API's answer envelope.
 *
 * Kept out of the component so the "is this answer complete enough to check?"
 * rule and the "what do we send?" rule live together -- CHECK is enabled
 * precisely when this returns non-null.
 */

import type { ExerciseDraft } from "@/components/exercises/ExerciseView";
import type { Exercise, SubmittedAnswer } from "@/types/api";

export function buildAnswer(exercise: Exercise, draft: ExerciseDraft): SubmittedAnswer | null {
  switch (exercise.type) {
    case "MULTIPLE_CHOICE":
    case "FILL_BLANK":
      return draft.choice === null ? null : { choice: draft.choice };

    case "TYPE_ANSWER":
      return draft.text.trim() === "" ? null : { text: draft.text };

    case "TRANSLATE_WORD_BANK": {
      if (draft.words.length === 0) return null;
      // Indices are resolved to words here rather than stored as words, because
      // a bank can contain the same word twice.
      const words = draft.words
        .map((index) => exercise.payload.word_bank[index])
        .filter((word): word is string => word !== undefined);
      return { words };
    }

    case "MATCH_PAIRS":
      // Only a fully matched board counts as an answer.
      return draft.match.pairs.length === exercise.payload.left.length
        ? { pairs: draft.match.pairs }
        : null;
  }
}

/**
 * The Spanish phrase this exercise is actually about, for the speaker button
 * to read aloud -- or `null` when speaking one would give the answer away.
 *
 * Three of the five types show their Spanish text as the *question*
 * (`payload.question`/`sentence`/`source_sentence`), so speaking it is safe
 * before an answer exists. The other two ask the learner to *produce* Spanish
 * (TYPE_ANSWER's `source_sentence` is the English prompt; MATCH_PAIRS mixes
 * both languages across many tiles), so there is no single unrevealing phrase
 * to speak and the button is omitted rather than guessed at.
 */
export function speakableText(exercise: Exercise): string | null {
  switch (exercise.type) {
    case "MULTIPLE_CHOICE":
      return exercise.payload.question;
    case "FILL_BLANK":
      return exercise.payload.sentence;
    case "TRANSLATE_WORD_BANK":
      return exercise.payload.source_sentence;
    case "TYPE_ANSWER":
    case "MATCH_PAIRS":
      return null;
  }
}
