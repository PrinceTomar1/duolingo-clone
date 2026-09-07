"use client";

import { useState } from "react";

import { Button } from "@/components/ui/Button";
import { Icon } from "@/components/ui/Icon";
import { PageHeader } from "@/components/ui/PageHeader";
import { api } from "@/lib/api";
import { clsx } from "@/lib/clsx";
import { useSessionStore } from "@/store/useSessionStore";
import { useThemeStore } from "@/store/useThemeStore";

/**
 * Settings, plus the demo controls.
 *
 * The day simulator is here rather than hidden because being able to *show*
 * the streak rule -- survive one quiet day, break on the second -- is the point
 * of the feature. It calls the backend's DEBUG-only endpoint, which simply does
 * not exist in a production build.
 */
export default function SettingsPage() {
  const theme = useThemeStore((state) => state.theme);
  const toggleTheme = useThemeStore((state) => state.toggle);
  const stats = useSessionStore((state) => state.stats);
  const refreshStats = useSessionStore((state) => state.refreshStats);
  const [simulated, setSimulated] = useState<string | null>(null);
  const [isBusy, setIsBusy] = useState(false);

  async function advanceDay(): Promise<void> {
    setIsBusy(true);
    try {
      const result = await api.advanceDay(1);
      setSimulated(result.simulated_today);
      await refreshStats();
    } catch {
      setSimulated("unavailable — the API is running with DEBUG off");
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <>
      <PageHeader title="Settings" />

      <section className="mb-4 rounded-2xl border-2 border-swan p-5 dark:border-night-border">
        <h2 className="mb-3 text-lg font-extrabold">Appearance</h2>
        <div className="flex items-center justify-between">
          <span className="flex items-center gap-2 text-sm font-bold text-wolf">
            <Icon name={theme === "dark" ? "moon" : "sun"} size={22} className="text-bee" />
            {theme === "dark" ? "Dark" : "Light"} theme
          </span>

          <button
            type="button"
            role="switch"
            aria-checked={theme === "dark"}
            aria-label="Toggle dark mode"
            onClick={toggleTheme}
            className={clsx(
              "relative h-8 w-14 rounded-full transition-colors duration-200",
              theme === "dark" ? "bg-feather" : "bg-swan",
            )}
          >
            <span
              className={clsx(
                "absolute top-1 h-6 w-6 rounded-full bg-snow shadow transition-transform duration-200",
                theme === "dark" ? "translate-x-7" : "translate-x-1",
              )}
            />
          </button>
        </div>
      </section>

      <section className="mb-4 rounded-2xl border-2 border-swan p-5 dark:border-night-border">
        <h2 className="mb-3 text-lg font-extrabold">Daily goal</h2>
        <p className="text-sm font-bold text-wolf">
          Currently {stats?.daily_goal_xp ?? 20} XP a day — {stats?.daily_xp_earned ?? 0} earned so far
          today.
        </p>
        <p className="mt-2 text-xs font-bold text-hare">
          The goal is stored per learner on `user_stats`; changing it from the UI is not part of this
          build.
        </p>
      </section>

      <section className="rounded-2xl border-2 border-beetle p-5">
        <h2 className="mb-1 flex items-center gap-2 text-lg font-extrabold text-beetle">
          <Icon name="clock" size={22} />
          Demo controls
        </h2>
        <p className="mb-4 text-sm font-bold text-wolf">
          Streaks are derived from the daily-XP ledger. Advance the clock one day and the streak
          survives; advance a second day with no lessons and it resets to zero.
        </p>

        <Button variant="secondary" size="lg" fullWidth disabled={isBusy} onClick={() => void advanceDay()}>
          {isBusy ? "Advancing…" : "Advance one day"}
        </Button>

        {simulated && (
          <p className="mt-3 text-center text-sm font-bold text-wolf">
            Simulated date: {simulated} — streak is now {stats?.current_streak ?? 0}
          </p>
        )}
      </section>
    </>
  );
}
