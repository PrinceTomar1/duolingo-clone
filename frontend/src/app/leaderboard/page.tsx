"use client";

import { useEffect, useState } from "react";

import { Avatar } from "@/components/ui/Avatar";
import { ErrorNotice } from "@/components/ui/ErrorNotice";
import { Icon } from "@/components/ui/Icon";
import { PageHeader } from "@/components/ui/PageHeader";
import { api } from "@/lib/api";
import { clsx } from "@/lib/clsx";
import { formatNumber } from "@/lib/format";
import { useSessionStore } from "@/store/useSessionStore";
import type { Leaderboard } from "@/types/api";

/**
 * The weekly league table.
 *
 * Ranked on XP earned in the last seven days, computed server-side from the
 * `daily_xp` ledger -- so a learner who joined yesterday can still place, which
 * an all-time ranking would never allow.
 */
export default function LeaderboardPage() {
  const user = useSessionStore((state) => state.user);
  const [board, setBoard] = useState<Leaderboard | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .leaderboard()
      .then(setBoard)
      .catch((cause: unknown) =>
        setError(cause instanceof Error ? cause.message : "Could not load the leaderboard"),
      );
  }, []);

  if (error) return <ErrorNotice message={error} />;
  if (!board) return <p className="py-10 text-center font-extrabold text-wolf">Loading…</p>;

  return (
    <>
      <PageHeader
        title="Leaderboard"
        subtitle={`XP earned between ${board.week_start} and ${board.week_end}`}
      />

      <div className="mb-6 rounded-2xl bg-bee px-5 py-4 text-center text-snow">
        <Icon name="trophy" size={44} className="mx-auto" strokeWidth={1.75} />
        <h2 className="mt-1 text-lg font-extrabold">Gold League</h2>
        <p className="text-xs font-bold opacity-90">Top 3 advance to the next league</p>
      </div>

      <ol className="space-y-2">
        {board.entries.map((entry) => {
          const isMe = entry.user_id === user?.id;
          return (
            <li
              key={entry.user_id}
              className={clsx(
                "flex items-center gap-3 rounded-2xl border-2 px-3 py-2.5 transition-colors",
                isMe
                  ? "border-macaw bg-macaw/10"
                  : "border-transparent hover:bg-polar dark:hover:bg-night-raised",
              )}
            >
              <span
                className={clsx(
                  "w-7 shrink-0 text-center text-base font-extrabold tabular-nums",
                  entry.rank <= 3 ? "text-bee" : "text-wolf",
                )}
              >
                {entry.rank}
              </span>

              <Avatar displayName={entry.display_name} color={entry.avatar_color} size={44} />

              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-extrabold">
                  {entry.display_name}
                  {isMe && <span className="ml-1.5 text-xs font-bold text-macaw">you</span>}
                </p>
                <p className="flex items-center gap-1 text-xs font-bold text-wolf">
                  <Icon name="flame" size={13} className="text-fox" />
                  {entry.current_streak} day streak
                </p>
              </div>

              <span className="shrink-0 text-sm font-extrabold tabular-nums text-wolf">
                {formatNumber(entry.weekly_xp)} XP
              </span>
            </li>
          );
        })}
      </ol>
    </>
  );
}
