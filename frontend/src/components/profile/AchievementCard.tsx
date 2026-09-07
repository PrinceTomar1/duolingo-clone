import { Icon } from "@/components/ui/Icon";
import { clsx } from "@/lib/clsx";
import { formatNumber } from "@/lib/format";
import type { Achievement } from "@/types/api";

/**
 * One badge row.
 *
 * Locked badges are shown greyed with their progress bar rather than hidden,
 * because the bar is the thing that makes the next one feel reachable.
 */
export function AchievementCard({ achievement }: { achievement: Achievement }) {
  const isUnlocked = achievement.unlocked_at !== null;
  const ratio = achievement.target > 0 ? achievement.progress / achievement.target : 0;

  return (
    <li className="flex items-center gap-4 rounded-2xl border-2 border-swan p-4 dark:border-night-border">
      <span
        className={clsx(
          "flex h-14 w-14 shrink-0 items-center justify-center rounded-xl",
          !isUnlocked && "opacity-40 grayscale",
        )}
        style={{ backgroundColor: `${achievement.color_hex}22`, color: achievement.color_hex }}
      >
        <Icon name={achievement.icon} size={30} />
      </span>

      <div className="min-w-0 flex-1">
        <p className={clsx("text-base font-extrabold", !isUnlocked && "text-wolf")}>
          {achievement.title}
        </p>
        <p className="truncate text-xs font-bold text-wolf">{achievement.description}</p>

        <div className="mt-2 flex items-center gap-2">
          <div className="h-2.5 flex-1 overflow-hidden rounded-full bg-swan dark:bg-night-border">
            <div
              className="h-full rounded-full transition-[width] duration-500"
              style={{
                width: `${Math.min(100, ratio * 100)}%`,
                backgroundColor: achievement.color_hex,
              }}
            />
          </div>
          <span className="shrink-0 text-xs font-extrabold tabular-nums text-wolf">
            {formatNumber(achievement.progress)}/{formatNumber(achievement.target)}
          </span>
        </div>
      </div>
    </li>
  );
}
