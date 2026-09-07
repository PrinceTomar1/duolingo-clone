"use client";

import { Button } from "@/components/ui/Button";
import { Icon } from "@/components/ui/Icon";
import { clsx } from "@/lib/clsx";
import type { AnswerResult } from "@/types/api";

/**
 * The bar that slides up from the bottom after CHECK.
 *
 * Green with a check circle when right; red with the correct answer spelled out
 * when wrong -- showing the answer is the entire point of the red state, so it
 * is never omitted.
 */
interface FeedbackBarProps {
  result: AnswerResult;
  isLastExercise: boolean;
  onContinue: () => void;
}

export function FeedbackBar({ result, isLastExercise, onContinue }: FeedbackBarProps) {
  const { is_correct: isCorrect } = result;

  return (
    <div
      role="status"
      aria-live="polite"
      className={clsx(
        "animate-slide-up border-t-2 px-4 py-4 sm:px-8 sm:py-6",
        isCorrect
          ? "border-transparent bg-correct-bg"
          : "border-transparent bg-incorrect-bg",
      )}
    >
      <div className="mx-auto flex max-w-2xl flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-3">
          <span
            className={clsx(
              "flex h-10 w-10 shrink-0 items-center justify-center rounded-full",
              isCorrect ? "bg-correct-text text-correct-bg" : "bg-incorrect-text text-incorrect-bg",
            )}
          >
            <Icon name={isCorrect ? "check" : "x"} size={22} strokeWidth={4} />
          </span>

          <div className={clsx("min-w-0", isCorrect ? "text-correct-text" : "text-incorrect-text")}>
            <p className="text-lg font-extrabold">
              {isCorrect ? "Nice!" : "Correct solution:"}
            </p>
            {!isCorrect && <p className="text-base font-bold">{result.correct_answer}</p>}
            {result.explanation && (
              <p className="mt-0.5 text-sm font-bold opacity-80">{result.explanation}</p>
            )}
          </div>
        </div>

        <Button
          variant={isCorrect ? "primary" : "danger"}
          size="lg"
          onClick={onContinue}
          className="w-full sm:w-auto sm:min-w-[10rem]"
        >
          {isLastExercise ? "Finish" : "Continue"}
        </Button>
      </div>
    </div>
  );
}
