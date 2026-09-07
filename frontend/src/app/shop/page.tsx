"use client";

import { useState } from "react";

import { Button } from "@/components/ui/Button";
import { HeartsDisplay } from "@/components/stats/HeartsDisplay";
import { Icon } from "@/components/ui/Icon";
import { PageHeader } from "@/components/ui/PageHeader";
import { ApiError, api } from "@/lib/api";
import { formatCountdown, formatNumber } from "@/lib/format";
import { useSessionStore } from "@/store/useSessionStore";

/**
 * The gem shop.
 *
 * Only the heart refill is real -- it spends gems against the server and the
 * new balance comes back from the API. The other two tiles are labelled as
 * unavailable rather than faked, so nothing here pretends to work.
 */
export default function ShopPage() {
  const stats = useSessionStore((state) => state.stats);
  const applyStats = useSessionStore((state) => state.applyStats);
  const user = useSessionStore((state) => state.user);
  const [message, setMessage] = useState<string | null>(null);
  const [isBusy, setIsBusy] = useState(false);

  async function refill(): Promise<void> {
    if (!user) return;
    setIsBusy(true);
    setMessage(null);
    try {
      applyStats(await api.refillHearts(user.id));
      setMessage("Hearts refilled.");
    } catch (cause) {
      setMessage(cause instanceof ApiError ? cause.message : "Could not refill hearts.");
    } finally {
      setIsBusy(false);
    }
  }

  if (!stats) return <p className="py-10 text-center font-extrabold text-wolf">Loading…</p>;

  const isFull = stats.hearts >= stats.max_hearts;
  const refillCost = stats.heart_refill_gem_cost;
  const canAfford = stats.gems >= refillCost;

  return (
    <>
      <PageHeader title="Shop" />

      <div className="mb-6 flex items-center justify-center gap-2 rounded-2xl border-2 border-swan py-4 dark:border-night-border">
        <Icon name="gem" size={30} className="text-macaw" />
        <span className="text-2xl font-extrabold tabular-nums">{formatNumber(stats.gems)}</span>
        <span className="text-sm font-bold text-wolf">gems</span>
      </div>

      <section className="mb-4 rounded-2xl border-2 border-swan p-5 dark:border-night-border">
        <div className="mb-3 flex items-start gap-4">
          <Icon name="heart" size={44} className="shrink-0 text-cardinal" />
          <div className="min-w-0 flex-1">
            <h2 className="text-lg font-extrabold">Refill hearts</h2>
            <p className="text-sm font-bold text-wolf">
              Get back to full so you can keep learning.
            </p>
            <div className="mt-2">
              <HeartsDisplay hearts={stats.hearts} max={stats.max_hearts} size={24} />
            </div>
            {!isFull && stats.seconds_until_next_heart !== null && (
              <p className="mt-1 text-xs font-bold text-hare">
                Next free heart in {formatCountdown(stats.seconds_until_next_heart)}
              </p>
            )}
          </div>
        </div>

        <Button
          variant="primary"
          size="lg"
          fullWidth
          disabled={isFull || !canAfford || isBusy}
          onClick={() => void refill()}
        >
          {isFull ? "Hearts are full" : `${formatNumber(refillCost)} gems`}
        </Button>

        {message && <p className="mt-3 text-center text-sm font-bold text-wolf">{message}</p>}
      </section>

      <h2 className="mb-3 mt-8 text-lg font-extrabold">Power-ups</h2>
      <div className="grid gap-3 sm:grid-cols-2">
        <UnavailableItem
          icon="flame"
          color="#FF9600"
          title="Streak freeze"
          description="Protects your streak for one missed day."
        />
        <UnavailableItem
          icon="infinity"
          color="#FF4B4B"
          title="Unlimited hearts"
          description="Never run out of hearts mid-lesson."
        />
      </div>
    </>
  );
}

interface UnavailableItemProps {
  icon: "flame" | "infinity";
  color: string;
  title: string;
  description: string;
}

/** A shop tile that is honest about not being implemented. */
function UnavailableItem({ icon, color, title, description }: UnavailableItemProps) {
  return (
    <div className="rounded-2xl border-2 border-swan p-4 opacity-70 dark:border-night-border">
      <Icon name={icon} size={32} style={{ color }} />
      <h3 className="mt-2 text-base font-extrabold">{title}</h3>
      <p className="text-xs font-bold text-wolf">{description}</p>
      <p className="mt-3 text-xs font-extrabold uppercase tracking-wide text-hare">
        Not part of this build
      </p>
    </div>
  );
}
