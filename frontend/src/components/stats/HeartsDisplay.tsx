import { Icon } from "@/components/ui/Icon";
import { clsx } from "@/lib/clsx";

/**
 * The heart bar.
 *
 * Renders `max` hearts always, greying out the spent ones, so the learner can
 * see how many they are down rather than just how many are left.
 */
interface HeartsDisplayProps {
  hearts: number;
  max: number;
  size?: number;
}

export function HeartsDisplay({ hearts, max, size = 22 }: HeartsDisplayProps) {
  return (
    <div className="flex items-center gap-0.5" aria-label={`${hearts} of ${max} hearts`}>
      {Array.from({ length: max }, (_, index) => (
        <Icon
          key={index}
          name="heart"
          size={size}
          className={clsx(
            "transition-colors duration-300",
            index < hearts ? "text-cardinal" : "text-swan dark:text-night-border",
          )}
        />
      ))}
    </div>
  );
}
