import { Icon } from "@/components/ui/Icon";
import type { IconName } from "@/lib/icon-paths";

/**
 * One icon-plus-number chip.
 *
 * The mobile top bar and the desktop right rail both show streak, gems and
 * hearts; this is that shared unit, so the two never drift apart visually.
 */
interface StatPillProps {
  icon: IconName;
  value: string | number;
  color: string;
  label: string;
  onClick?: () => void;
}

export function StatPill({ icon, value, color, label, onClick }: StatPillProps) {
  const content = (
    <>
      <Icon name={icon} size={26} className={color} />
      <span className="text-base font-extrabold tabular-nums">{value}</span>
    </>
  );

  // Rendered as a button only when it does something, so a decorative pill does
  // not land in the keyboard tab order.
  if (onClick) {
    return (
      <button
        type="button"
        onClick={onClick}
        aria-label={label}
        className="flex items-center gap-1.5 rounded-xl px-2 py-1 transition-colors hover:bg-polar dark:hover:bg-night-raised"
      >
        {content}
      </button>
    );
  }

  return (
    <div className="flex items-center gap-1.5 px-2 py-1" aria-label={label}>
      {content}
    </div>
  );
}
