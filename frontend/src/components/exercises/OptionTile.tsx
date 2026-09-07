"use client";

import { clsx } from "@/lib/clsx";

/**
 * The selectable card shared by multiple-choice and fill-in-the-blank.
 *
 * One component for both because they are the same interaction -- pick one of
 * N -- and the graded states (selected, correct, wrong) must look identical
 * across them.
 */
export type TileState = "idle" | "selected" | "correct" | "wrong";

const STATES: Record<TileState, string> = {
  idle: "border-swan border-b-4 bg-snow text-eel hover:bg-polar dark:border-night-border dark:bg-night-raised dark:text-swan dark:hover:bg-night",
  selected: "border-macaw border-b-4 bg-macaw/10 text-humpback dark:text-macaw",
  correct: "border-feather border-b-4 bg-correct-bg text-correct-text",
  wrong: "border-cardinal border-b-4 bg-incorrect-bg text-incorrect-text animate-shake",
};

interface OptionTileProps {
  label: string;
  state: TileState;
  disabled?: boolean;
  onClick: () => void;
  /** Duolingo numbers the choices so they can be picked with the keyboard. */
  hotkey?: number;
}

export function OptionTile({ label, state, disabled, onClick, hotkey }: OptionTileProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      aria-pressed={state === "selected"}
      className={clsx(
        "flex w-full items-center gap-3 rounded-2xl border-2 px-4 py-3.5 text-left text-base font-bold transition-colors duration-100",
        disabled && state === "idle" ? "opacity-60" : "",
        STATES[state],
      )}
    >
      {hotkey !== undefined && (
        <span className="hidden h-6 w-6 shrink-0 items-center justify-center rounded-md border-2 border-current text-xs opacity-60 sm:flex">
          {hotkey}
        </span>
      )}
      <span className="min-w-0 flex-1">{label}</span>
    </button>
  );
}
