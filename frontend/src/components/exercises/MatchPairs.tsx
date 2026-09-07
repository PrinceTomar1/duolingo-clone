"use client";

import { clsx } from "@/lib/clsx";
import type { MatchPairsPayload } from "@/types/api";

/**
 * Two columns, tap a Spanish tile then its English match.
 *
 * The board needs live feedback on each link, but the client is never given
 * the mapping. So this component only *routes* taps: it tracks which left tile
 * is pending and hands each attempted link to `onPair`, which asks the server.
 * One bit comes back per tap -- exactly what the game would show anyway -- and
 * the answer key stays on the server.
 */

export interface MatchState {
  /** The left tile currently awaiting a partner. */
  pendingLeft: string | null;
  /** Left tiles that have been correctly matched and faded out. */
  solved: string[];
  /** The pair flashing red, cleared on the next tap. */
  wrong: [string, string] | null;
  /** Confirmed pairs, in the shape the API expects. */
  pairs: Array<{ left: string; right: string }>;
}

export const EMPTY_MATCH_STATE: MatchState = {
  pendingLeft: null,
  solved: [],
  wrong: null,
  pairs: [],
};

interface MatchPairsProps {
  payload: MatchPairsPayload;
  state: MatchState;
  /** Asks the server whether this link is right, then updates the board. */
  onPair: (left: string, right: string) => void;
  onChange: (state: MatchState) => void;
}

export function MatchPairs({ payload, state, onPair, onChange }: MatchPairsProps) {
  function tapLeft(left: string): void {
    if (state.solved.includes(left)) return;
    onChange({ ...state, pendingLeft: left, wrong: null });
  }

  function tapRight(right: string): void {
    const left = state.pendingLeft;
    // Ignore a right-tile tap with nothing selected, and ignore an already
    // matched tile, so a stray tap can never corrupt the board.
    if (!left || state.pairs.some((pair) => pair.right === right)) return;
    onPair(left, right);
  }

  return (
    <div className="w-full">
      <div className="grid grid-cols-2 gap-3 sm:gap-6">
        <div className="flex flex-col gap-3">
          {payload.left.map((left) => (
            <Tile
              key={left}
              label={left}
              isSelected={state.pendingLeft === left}
              isSolved={state.solved.includes(left)}
              isWrong={state.wrong?.[0] === left}
              onClick={() => tapLeft(left)}
            />
          ))}
        </div>
        <div className="flex flex-col gap-3">
          {payload.right.map((right) => (
            <Tile
              key={right}
              label={right}
              isSelected={false}
              isSolved={state.pairs.some((pair) => pair.right === right)}
              isWrong={state.wrong?.[1] === right}
              onClick={() => tapRight(right)}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

interface TileProps {
  label: string;
  isSelected: boolean;
  isSolved: boolean;
  isWrong: boolean;
  onClick: () => void;
}

function Tile({ label, isSelected, isSolved, isWrong, onClick }: TileProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={isSolved}
      aria-pressed={isSelected}
      className={clsx(
        "rounded-2xl border-2 border-b-4 px-3 py-4 text-sm font-bold transition-all duration-200 sm:text-base",
        // A solved pair flashes green then fades to an empty slot, which is how
        // the real game clears the board without collapsing the layout.
        isSolved && "border-feather bg-correct-bg text-transparent opacity-0",
        isWrong && "animate-shake border-cardinal bg-incorrect-bg text-incorrect-text",
        isSelected && "border-macaw bg-macaw/10 ring-2 ring-macaw",
        !isSolved && !isWrong && !isSelected &&
          "border-swan bg-snow text-eel hover:bg-polar dark:border-night-border dark:bg-night-raised dark:text-swan dark:hover:bg-night",
      )}
    >
      {label}
    </button>
  );
}
