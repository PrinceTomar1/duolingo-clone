"use client";

import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { HeartsDisplay } from "@/components/stats/HeartsDisplay";
import { Icon } from "@/components/ui/Icon";
import { formatCountdown, formatNumber } from "@/lib/format";

/**
 * Shown when the last heart is spent mid-lesson.
 *
 * Offers the two real ways out -- spend gems, or wait for regeneration -- and
 * says exactly how long the wait is, using the server's countdown rather than a
 * guess.
 */
interface OutOfHeartsModalProps {
  gems: number;
  refillCost: number;
  secondsUntilNextHeart: number | null;
  isRefilling: boolean;
  onRefill: () => void;
  onQuit: () => void;
}

export function OutOfHeartsModal({
  gems,
  refillCost,
  secondsUntilNextHeart,
  isRefilling,
  onRefill,
  onQuit,
}: OutOfHeartsModalProps) {
  const canAfford = gems >= refillCost;

  return (
    <Modal title="You ran out of hearts!" onClose={onQuit} accentColor="#FF4B4B" icon="heart">
      <div className="mb-4 flex justify-center">
        <HeartsDisplay hearts={0} max={5} size={30} />
      </div>

      <p className="mb-6 text-center text-sm font-bold text-wolf">
        {secondsUntilNextHeart === null
          ? "Refill to keep going."
          : `Your next heart arrives in ${formatCountdown(secondsUntilNextHeart)}.`}
      </p>

      <div className="flex flex-col gap-3">
        <Button variant="primary" size="lg" fullWidth onClick={onRefill} disabled={!canAfford || isRefilling}>
          <span className="flex items-center justify-center gap-2">
            <Icon name="gem" size={20} />
            {isRefilling ? "Refilling…" : `Refill for ${formatNumber(refillCost)}`}
          </span>
        </Button>
        {!canAfford && (
          <p className="text-center text-xs font-bold text-cardinal">
            You have {formatNumber(gems)} gems — {formatNumber(refillCost - gems)} short.
          </p>
        )}
        <Button variant="ghost" size="lg" fullWidth onClick={onQuit}>
          End session
        </Button>
      </div>
    </Modal>
  );
}
