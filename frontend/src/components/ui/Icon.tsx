import { ICONS, resolveIcon, type IconName } from "@/lib/icon-paths";

/**
 * Renders one glyph from the icon table.
 *
 * Colour always comes from `currentColor`, so an icon inherits whatever text
 * colour its container sets and never needs a colour prop of its own.
 */

interface IconProps {
  name: IconName | string;
  size?: number;
  className?: string;
  strokeWidth?: number;
  /** For colours that come from the API (unit and achievement hexes) and so
      cannot be expressed as a Tailwind class. */
  style?: React.CSSProperties;
}

export function Icon({ name, size = 24, className, strokeWidth = 2, style }: IconProps) {
  const definition = ICONS[resolveIcon(name)];

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill={definition.filled ? "currentColor" : "none"}
      stroke={definition.filled ? "none" : "currentColor"}
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      style={style}
      aria-hidden="true"
      focusable="false"
    >
      {definition.paths.map((d) => (
        <path key={d} d={d} />
      ))}
    </svg>
  );
}
