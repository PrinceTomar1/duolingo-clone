"use client";

import { useEffect, useRef } from "react";

import { clsx } from "@/lib/clsx";
import type { AnswerResult, TypeAnswerPayload } from "@/types/api";

/**
 * Free-typing translation.
 *
 * The server folds case, accents and punctuation before comparing, so no
 * client-side normalisation happens here -- doing it in both places would be
 * two rules that could disagree.
 */
interface TypeAnswerProps {
  payload: TypeAnswerPayload;
  value: string;
  result: AnswerResult | null;
  onChange: (text: string) => void;
  onSubmit: () => void;
}

export function TypeAnswer({ payload, value, result, onChange, onSubmit }: TypeAnswerProps) {
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Focus on mount and whenever a new exercise of this type appears, so the
  // learner can just start typing.
  useEffect(() => {
    inputRef.current?.focus();
  }, [payload.source_sentence]);

  return (
    <div className="w-full">
      <p className="mb-6 text-center text-2xl font-extrabold sm:text-3xl">
        {payload.source_sentence}
      </p>

      <textarea
        ref={inputRef}
        data-testid="type-answer"
        value={value}
        rows={3}
        spellCheck={false}
        autoComplete="off"
        disabled={result !== null}
        placeholder="Type in Spanish…"
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={(event) => {
          // Enter checks the answer; Shift+Enter is left alone so the field
          // still behaves like a textarea.
          if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            onSubmit();
          }
        }}
        className={clsx(
          "w-full resize-none rounded-2xl border-2 bg-snow p-4 text-lg font-bold outline-none transition-colors dark:bg-night-raised",
          "placeholder:font-bold placeholder:text-hare",
          result === null && "border-swan focus:border-macaw dark:border-night-border",
          result?.is_correct === true && "border-feather bg-correct-bg text-correct-text",
          result?.is_correct === false && "border-cardinal bg-incorrect-bg text-incorrect-text",
        )}
      />
    </div>
  );
}
