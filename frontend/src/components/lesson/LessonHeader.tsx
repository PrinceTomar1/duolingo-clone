"use client";

import { HeartsDisplay } from "@/components/stats/HeartsDisplay";
import { Icon } from "@/components/ui/Icon";

/**
 * The lesson player's top row: quit, progress, hearts.
 *
 * The bar animates on `width` alone with a 300ms transition, so each answered
 * exercise visibly pushes it forward rather than jumping.
 */
interface LessonHeaderProps {
  /** 0 to 1. */
  progress: number;
  hearts: number;
  maxHearts: number;
  onQuit: () => void;
}

export function LessonHeader({ progress, hearts, maxHearts, onQuit }: LessonHeaderProps) {
  return (
    <header className="flex items-center gap-3 px-4 py-4 sm:gap-5">
      <button
        type="button"
        onClick={onQuit}
        aria-label="Quit lesson"
        className="shrink-0 rounded-lg p-1 text-hare transition-colors hover:text-wolf"
      >
        <Icon name="x" size={28} strokeWidth={3} />
      </button>

      <div
        className="h-4 flex-1 overflow-hidden rounded-full bg-swan dark:bg-night-raised"
        role="progressbar"
        aria-valuenow={Math.round(progress * 100)}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <div
          className="relative h-full rounded-full bg-feather transition-[width] duration-300"
          style={{ width: `${Math.max(progress * 100, 3)}%` }}
        >
          {/* The lighter highlight along the top of the fill, which is what
              gives Duolingo's progress bar its glossy look. */}
          <span className="absolute inset-x-1.5 top-1 h-1 rounded-full bg-white/30" />
        </div>
      </div>

      <div className="shrink-0">
        <HeartsDisplay hearts={hearts} max={maxHearts} size={24} />
      </div>
    </header>
  );
}
