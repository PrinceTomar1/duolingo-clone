import { weekdayLabel } from "@/lib/format";
import type { DailyXp } from "@/types/api";

/**
 * The last two weeks of the `daily_xp` ledger, as bars.
 *
 * Heights are relative to the busiest day rather than to a fixed maximum, so
 * the shape of a quiet fortnight is still readable. Gaps in the ledger simply
 * do not render a bar, which is exactly what a broken streak looks like.
 */
export function ActivityChart({ activity }: { activity: DailyXp[] }) {
  if (activity.length === 0) {
    return <p className="text-sm font-bold text-wolf">No activity yet — finish a lesson to start.</p>;
  }

  const peak = Math.max(...activity.map((day) => day.xp_earned), 1);

  return (
    <div className="flex items-end gap-1.5 overflow-x-auto no-scrollbar sm:gap-2">
      {activity.map((day) => (
        <div key={day.date} className="flex min-w-[1.75rem] flex-1 flex-col items-center gap-1">
          <span className="text-[10px] font-extrabold tabular-nums text-wolf">{day.xp_earned}</span>
          <div
            title={`${day.date}: ${day.xp_earned} XP`}
            style={{ height: `${Math.max(6, (day.xp_earned / peak) * 100)}px` }}
            className="w-full rounded-t-md bg-feather transition-[height] duration-500"
          />
          <span className="text-[10px] font-bold text-hare">{weekdayLabel(day.date)}</span>
        </div>
      ))}
    </div>
  );
}
