import { Icon } from "@/components/ui/Icon";
import { ProgressRing } from "@/components/ui/ProgressRing";

/**
 * The daily-goal ring.
 *
 * Fills from today's entry in the `daily_xp` ledger, so it resets at midnight
 * without any client-side date arithmetic -- the server simply starts reporting
 * a new day's total.
 */
interface DailyGoalRingProps {
  earned: number;
  goal: number;
  size?: number;
}

export function DailyGoalRing({ earned, goal, size = 72 }: DailyGoalRingProps) {
  const progress = goal > 0 ? earned / goal : 0;
  const isComplete = earned >= goal;

  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <ProgressRing
        progress={progress}
        size={size}
        strokeWidth={7}
        color={isComplete ? "#58CC02" : "#FFC800"}
        trackColor="#E5E5E5"
      />
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        {isComplete ? (
          <Icon name="check" size={size * 0.4} className="text-feather" strokeWidth={3} />
        ) : (
          <>
            <span className="text-sm font-extrabold leading-none tabular-nums">{earned}</span>
            <span className="text-[10px] font-bold leading-none text-wolf">/{goal}</span>
          </>
        )}
      </div>
    </div>
  );
}
