"use client";

import { OptionTile, type TileState } from "@/components/exercises/OptionTile";
import type { AnswerResult, FillBlankPayload } from "@/types/api";

/**
 * Complete a sentence from three options.
 *
 * The blank is rendered as an inline slot that fills with the picked word, so
 * the learner reads the finished sentence back before checking it.
 */
interface FillBlankProps {
  payload: FillBlankPayload;
  selected: string | null;
  result: AnswerResult | null;
  onSelect: (choice: string) => void;
}

export function FillBlank({ payload, selected, result, onSelect }: FillBlankProps) {
  const [before, after] = payload.sentence.split("___");

  function stateFor(option: string): TileState {
    if (!result) return option === selected ? "selected" : "idle";
    if (option === result.correct_answer) return "correct";
    if (option === selected) return "wrong";
    return "idle";
  }

  return (
    <div className="w-full">
      <p className="mb-2 text-center text-2xl font-extrabold leading-relaxed sm:text-3xl">
        {before}
        <span className="mx-1 inline-block min-w-[5rem] border-b-4 border-swan pb-0.5 text-center text-macaw dark:border-night-border">
          {selected ?? " "}
        </span>
        {after}
      </p>
      <p className="mb-6 text-center text-sm font-bold text-wolf">{payload.translation}</p>

      <div className="grid gap-3 sm:grid-cols-3">
        {payload.options.map((option) => (
          <OptionTile
            key={option}
            label={option}
            state={stateFor(option)}
            disabled={result !== null}
            onClick={() => onSelect(option)}
          />
        ))}
      </div>
    </div>
  );
}
