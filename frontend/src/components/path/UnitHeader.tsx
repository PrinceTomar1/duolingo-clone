import { Icon } from "@/components/ui/Icon";

/**
 * The full-width coloured bar that introduces each unit.
 *
 * Sticky so the learner always knows which unit they are scrolled into, which
 * is exactly what the real app does on a long path.
 */
interface UnitHeaderProps {
  title: string;
  description: string;
  color: string;
}

export function UnitHeader({ title, description, color }: UnitHeaderProps) {
  return (
    <div
      className="sticky top-12 z-10 mb-8 flex items-center justify-between rounded-2xl px-4 py-3 text-snow shadow-sm xl:top-2"
      style={{ backgroundColor: color }}
    >
      <div className="min-w-0">
        <p className="text-xs font-extrabold uppercase tracking-widest opacity-90">{title}</p>
        <h2 className="truncate text-lg font-extrabold">{description}</h2>
      </div>
      {/* The guidebook is out of scope. It is kept because the header reads
          wrong without it, but it is genuinely inert rather than a live-looking
          control that swallows taps: disabled, dimmed, and named as unavailable
          so the reason reaches a screen reader and a touch user too -- a title
          tooltip alone never shows on a phone. */}
      <button
        type="button"
        disabled
        aria-label="Guidebook — not part of this build"
        title="Guidebook — not part of this build"
        className="ml-3 shrink-0 cursor-not-allowed rounded-xl border-2 border-white/25 p-2 opacity-50"
      >
        <Icon name="book" size={22} />
      </button>
    </div>
  );
}
