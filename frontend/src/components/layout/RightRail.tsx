"use client";

import Link from "next/link";

import { DailyGoalRing } from "@/components/stats/DailyGoalRing";
import { HeartsDisplay } from "@/components/stats/HeartsDisplay";
import { Icon } from "@/components/ui/Icon";
import { formatCountdown, formatNumber } from "@/lib/format";
import { useSessionStore } from "@/store/useSessionStore";

/**
 * The desktop right rail (>=1280px).
 *
 * Everything here is a read of the session store, so a lesson that changes
 * hearts or XP updates the rail without any page-level plumbing.
 */
export function RightRail() {
  const stats = useSessionStore((state) => state.stats);
  if (!stats) return null;

  return (
    <aside className="fixed inset-y-0 right-0 z-20 hidden w-[22rem] flex-col gap-5 overflow-y-auto border-l-2 border-swan bg-snow px-6 py-6 dark:border-night-border dark:bg-night xl:flex">
      <div className="flex items-center justify-between rounded-2xl border-2 border-swan px-4 py-3 dark:border-night-border">
        <div className="flex items-center gap-2">
          <Icon name="flame" size={28} className="text-fox" />
          <span className="text-lg font-extrabold tabular-nums">{stats.current_streak}</span>
        </div>
        <div className="flex items-center gap-2">
          <Icon name="gem" size={26} className="text-macaw" />
          <span className="text-lg font-extrabold tabular-nums">{formatNumber(stats.gems)}</span>
        </div>
        <HeartsDisplay hearts={stats.hearts} max={stats.max_hearts} />
      </div>

      <section className="rounded-2xl border-2 border-swan p-4 dark:border-night-border">
        <h2 className="mb-3 text-base font-extrabold uppercase tracking-wide">Daily quest</h2>
        <div className="flex items-center gap-4">
          <DailyGoalRing earned={stats.daily_xp_earned} goal={stats.daily_goal_xp} />
          <div>
            <p className="text-sm font-extrabold">Earn {stats.daily_goal_xp} XP</p>
            <p className="text-xs font-bold text-wolf">
              {stats.daily_xp_earned >= stats.daily_goal_xp
                ? "Goal complete — nice work"
                : `${stats.daily_goal_xp - stats.daily_xp_earned} XP to go`}
            </p>
          </div>
        </div>
      </section>

      <section className="rounded-2xl border-2 border-swan p-4 dark:border-night-border">
        <h2 className="mb-3 text-base font-extrabold uppercase tracking-wide">Your stats</h2>
        <dl className="space-y-2 text-sm font-bold">
          <div className="flex items-center justify-between">
            <dt className="flex items-center gap-2 text-wolf">
              <Icon name="bolt" size={20} className="text-bee" /> Total XP
            </dt>
            <dd className="tabular-nums">{formatNumber(stats.total_xp)}</dd>
          </div>
          <div className="flex items-center justify-between">
            <dt className="flex items-center gap-2 text-wolf">
              <Icon name="bolt" size={20} className="text-macaw" /> This week
            </dt>
            <dd className="tabular-nums">{formatNumber(stats.weekly_xp)}</dd>
          </div>
          <div className="flex items-center justify-between">
            <dt className="flex items-center gap-2 text-wolf">
              <Icon name="flame" size={20} className="text-fox" /> Longest streak
            </dt>
            <dd className="tabular-nums">{stats.longest_streak} days</dd>
          </div>
          {stats.seconds_until_next_heart !== null && (
            <div className="flex items-center justify-between">
              <dt className="flex items-center gap-2 text-wolf">
                <Icon name="heart" size={20} className="text-cardinal" /> Next heart
              </dt>
              <dd className="tabular-nums">{formatCountdown(stats.seconds_until_next_heart)}</dd>
            </div>
          )}
        </dl>
      </section>

      {stats.hearts < stats.max_hearts && (
        <Link
          href="/shop"
          className="rounded-2xl border-2 border-swan p-4 text-center transition-colors hover:bg-polar dark:border-night-border dark:hover:bg-night-raised"
        >
          <p className="text-sm font-extrabold">Running low on hearts?</p>
          <p className="text-xs font-bold text-macaw">Refill them in the shop →</p>
        </Link>
      )}
    </aside>
  );
}
