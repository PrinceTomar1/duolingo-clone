"use client";

import { HeartsDisplay } from "@/components/stats/HeartsDisplay";
import { StatPill } from "@/components/stats/StatPill";
import { formatNumber } from "@/lib/format";
import { useSessionStore } from "@/store/useSessionStore";

/**
 * The sticky top bar that replaces the right rail below 1280px.
 *
 * Sticky rather than fixed so it scrolls away with the unit header and comes
 * back on scroll-up, which keeps the small viewport's vertical budget for the
 * path itself.
 */
export function MobileTopBar() {
  const stats = useSessionStore((state) => state.stats);
  if (!stats) return null;

  return (
    <div className="sticky top-0 z-20 flex items-center justify-between border-b-2 border-swan bg-snow px-3 py-2 dark:border-night-border dark:bg-night xl:hidden">
      <StatPill icon="flame" value={stats.current_streak} color="text-fox" label="Day streak" />
      <StatPill icon="gem" value={formatNumber(stats.gems)} color="text-macaw" label="Gems" />
      <HeartsDisplay hearts={stats.hearts} max={stats.max_hearts} />
    </div>
  );
}
