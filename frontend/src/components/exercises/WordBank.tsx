"use client";

import { motion } from "framer-motion";

import { clsx } from "@/lib/clsx";
import type { AnswerResult, WordBankPayload } from "@/types/api";

/**
 * Tap words to build a translation.
 *
 * Tiles are tracked by their index in the bank, not by their text, because a
 * bank legitimately contains the same word twice -- keying on the string would
 * make both copies move as one.
 *
 * The "flying" effect is framer-motion's `layoutId`: the same id on the bank
 * tile and the answer-line tile makes the library animate one into the other's
 * position, leaving a grey slot behind.
 */
interface WordBankProps {
  payload: WordBankPayload;
  /** Indices into `payload.word_bank`, in the order they were tapped. */
  chosen: number[];
  result: AnswerResult | null;
  onChange: (chosen: number[]) => void;
}

export function WordBank({ payload, chosen, result, onChange }: WordBankProps) {
  const isLocked = result !== null;

  return (
    <div className="w-full">
      <p className="mb-5 text-center text-xl font-extrabold sm:text-2xl">
        {payload.source_sentence}
      </p>

      {/* The answer line: two ruled rows the tiles land on. */}
      <div
        className={clsx(
          "mb-8 flex min-h-[7rem] flex-wrap content-start gap-2 border-y-2 py-3",
          isLocked && result?.is_correct === false ? "border-cardinal" : "border-swan dark:border-night-border",
        )}
      >
        {chosen.map((bankIndex) => (
          <motion.button
            key={bankIndex}
            layoutId={`tile-${bankIndex}`}
            type="button"
            disabled={isLocked}
            onClick={() => onChange(chosen.filter((item) => item !== bankIndex))}
            className="rounded-xl border-2 border-swan border-b-4 bg-snow px-3 py-2 font-bold dark:border-night-border dark:bg-night-raised"
          >
            {payload.word_bank[bankIndex]}
          </motion.button>
        ))}
      </div>

      <div className="flex flex-wrap justify-center gap-2">
        {payload.word_bank.map((word, bankIndex) => {
          const isUsed = chosen.includes(bankIndex);
          return (
            <div key={bankIndex} className="relative">
              {/* The grey slot the tile leaves behind. Rendered always and made
                  invisible when unused, so the bank never reflows on a tap. */}
              <span
                aria-hidden="true"
                className={clsx(
                  "block rounded-xl border-2 border-b-4 px-3 py-2 font-bold",
                  isUsed
                    ? "border-swan bg-swan text-transparent dark:border-night-border dark:bg-night-border"
                    : "invisible",
                )}
              >
                {word}
              </span>

              {!isUsed && (
                <motion.button
                  layoutId={`tile-${bankIndex}`}
                  type="button"
                  disabled={isLocked}
                  onClick={() => onChange([...chosen, bankIndex])}
                  className="absolute inset-0 rounded-xl border-2 border-swan border-b-4 bg-snow px-3 py-2 font-bold transition-colors hover:bg-polar disabled:opacity-60 dark:border-night-border dark:bg-night-raised dark:hover:bg-night"
                >
                  {word}
                </motion.button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
