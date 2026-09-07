"use client";

import { OptionTile, type TileState } from "@/components/exercises/OptionTile";
import type { AnswerResult, MultipleChoicePayload } from "@/types/api";

/**
 * Pick the right translation from four options.
 *
 * After checking, the chosen tile turns green or red and -- when wrong -- the
 * server's revealed answer is highlighted green, so the learner sees the
 * correction in place rather than only in the feedback bar.
 */
interface MultipleChoiceProps {
  payload: MultipleChoicePayload;
  selected: string | null;
  result: AnswerResult | null;
  onSelect: (choice: string) => void;
}

export function MultipleChoice({ payload, selected, result, onSelect }: MultipleChoiceProps) {
  function stateFor(option: string): TileState {
    if (!result) return option === selected ? "selected" : "idle";
    if (option === result.correct_answer) return "correct";
    if (option === selected) return "wrong";
    return "idle";
  }

  return (
    <div className="w-full">
      <p className="mb-5 text-center text-2xl font-extrabold sm:text-3xl">{payload.question}</p>
      <div className="grid gap-3 sm:grid-cols-2">
        {payload.options.map((option, index) => (
          <OptionTile
            key={option}
            label={option}
            hotkey={index + 1}
            state={stateFor(option)}
            disabled={result !== null}
            onClick={() => onSelect(option)}
          />
        ))}
      </div>
    </div>
  );
}
