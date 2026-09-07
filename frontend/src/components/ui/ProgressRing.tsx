/**
 * The crown ring drawn around a path node.
 *
 * An SVG circle whose `stroke-dasharray` is the full circumference and whose
 * `stroke-dashoffset` hides the unearned portion -- the standard trick for a
 * radial progress bar without a chart library. Rotated -90deg so it fills from
 * twelve o'clock rather than three.
 */

interface ProgressRingProps {
  /** 0 to 1. Values outside that are clamped rather than drawn incorrectly. */
  progress: number;
  size: number;
  strokeWidth: number;
  color: string;
  trackColor: string;
  className?: string;
}

export function ProgressRing({
  progress,
  size,
  strokeWidth,
  color,
  trackColor,
  className,
}: ProgressRingProps) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const clamped = Math.min(1, Math.max(0, progress));

  return (
    <svg
      width={size}
      height={size}
      viewBox={`0 0 ${size} ${size}`}
      className={className}
      aria-hidden="true"
    >
      <g transform={`rotate(-90 ${size / 2} ${size / 2})`}>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={trackColor}
          strokeWidth={strokeWidth}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={circumference * (1 - clamped)}
          className="transition-[stroke-dashoffset] duration-500"
        />
      </g>
    </svg>
  );
}
