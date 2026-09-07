"use client";

import { FillBlank } from "@/components/exercises/FillBlank";
import { MatchPairs, type MatchState } from "@/components/exercises/MatchPairs";
import { MultipleChoice } from "@/components/exercises/MultipleChoice";
import { TypeAnswer } from "@/components/exercises/TypeAnswer";
import { WordBank } from "@/components/exercises/WordBank";
import type { AnswerResult, Exercise } from "@/types/api";

/**
 * Renders whichever exercise type is current.
 *
 * The switch is exhaustive over `Exercise`, which is a discriminated union, so
 * adding a sixth type to `types/api.ts` turns this into a compile error until
 * it is handled here. That is the point of the union: the compiler, not a code
 * review, catches the missing case.
 */

/** The per-type draft the player holds while an exercise is in progress. */
export interface ExerciseDraft {
  choice: string | null;
  text: string;
  /** Indices into the word bank, in tap order. */
  words: number[];
  match: MatchState;
}

interface ExerciseViewProps {
  exercise: Exercise;
  draft: ExerciseDraft;
  result: AnswerResult | null;
  onDraftChange: (draft: ExerciseDraft) => void;
  onSubmit: () => void;
  onPair: (left: string, right: string) => void;
}

export function ExerciseView({
  exercise,
  draft,
  result,
  onDraftChange,
  onSubmit,
  onPair,
}: ExerciseViewProps) {
  switch (exercise.type) {
    case "MULTIPLE_CHOICE":
      return (
        <MultipleChoice
          payload={exercise.payload}
          selected={draft.choice}
          result={result}
          onSelect={(choice) => onDraftChange({ ...draft, choice })}
        />
      );

    case "FILL_BLANK":
      return (
        <FillBlank
          payload={exercise.payload}
          selected={draft.choice}
          result={result}
          onSelect={(choice) => onDraftChange({ ...draft, choice })}
        />
      );

    case "TRANSLATE_WORD_BANK":
      return (
        <WordBank
          payload={exercise.payload}
          chosen={draft.words}
          result={result}
          onChange={(words) => onDraftChange({ ...draft, words })}
        />
      );

    case "TYPE_ANSWER":
      return (
        <TypeAnswer
          payload={exercise.payload}
          value={draft.text}
          result={result}
          onChange={(text) => onDraftChange({ ...draft, text })}
          onSubmit={onSubmit}
        />
      );

    case "MATCH_PAIRS":
      return (
        <MatchPairs
          payload={exercise.payload}
          state={draft.match}
          onPair={onPair}
          onChange={(match) => onDraftChange({ ...draft, match })}
        />
      );
  }
}
