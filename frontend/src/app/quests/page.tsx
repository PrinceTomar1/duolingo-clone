"use client";

import { DailyGoalRing } from "@/components/stats/DailyGoalRing";
import { Icon } from "@/components/ui/Icon";
import { PageHeader } from "@/components/ui/PageHeader";
import { useSessionStore } from "@/store/useSessionStore";

/**
 * Quests.
 *
 * Every quest here is driven by persisted state. The daily quest reads today's
 * row from the ledger -- the same source the right rail's ring uses -- and the
 * two weekly quests read `weekly_xp` (summed from the last seven ledger days)
 * and the streak. Nothing on this screen invents progress the backend does not
 * track; a quest the API could not answer would be shown as unavailable rather
 * than faked.
 */
export default function QuestsPage() {
  const stats = useSessionStore((state) => state.stats);

  if (!stats) return <p className="py-10 text-center font-extrabold text-wolf">Loading…</p>;

  const isComplete = stats.daily_xp_earned >= stats.daily_goal_xp;

  return (
    <>
      <PageHeader title="Quests" subtitle="Daily goals reset at midnight" />

      <section className="mb-6 flex items-center gap-5 rounded-2xl border-2 border-swan p-5 dark:border-night-border">
        <DailyGoalRing earned={stats.daily_xp_earned} goal={stats.daily_goal_xp} size={88} />
        <div className="min-w-0">
          <h2 className="text-lg font-extrabold">Earn {stats.daily_goal_xp} XP</h2>
          <p className="text-sm font-bold text-wolf">
            {isComplete
              ? "Done for today — anything else is a bonus."
              : `${stats.daily_goal_xp - stats.daily_xp_earned} XP to go.`}
          </p>
          <p className="mt-1 flex items-center gap-1 text-xs font-bold text-fox">
            <Icon name="flame" size={14} />
            {stats.current_streak} day streak on the line
          </p>
        </div>
      </section>

      <h2 className="mb-3 text-lg font-extrabold">Weekly quests</h2>
      <ul className="space-y-3">
        {[
          { title: "Earn 500 XP this week", progress: stats.weekly_xp, target: 500 },
          { title: "Reach a 14 day streak", progress: stats.current_streak, target: 14 },
        ].map((quest) => (
          <li key={quest.title} className="rounded-2xl border-2 border-swan p-4 dark:border-night-border">
            <div className="mb-2 flex items-baseline justify-between">
              <p className="text-sm font-extrabold">{quest.title}</p>
              <span className="text-xs font-extrabold tabular-nums text-wolf">
                {Math.min(quest.progress, quest.target)}/{quest.target}
              </span>
            </div>
            <div className="h-3 overflow-hidden rounded-full bg-swan dark:bg-night-border">
              <div
                className="h-full rounded-full bg-bee transition-[width] duration-500"
                style={{ width: `${Math.min(100, (quest.progress / quest.target) * 100)}%` }}
              />
            </div>
          </li>
        ))}
      </ul>
    </>
  );
}
