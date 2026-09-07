/**
 * A learner's avatar.
 *
 * There are no uploaded images in this build, so the avatar is the learner's
 * initial on the colour stored with their row -- deterministic, zero assets,
 * and every learner is visually distinct.
 */
interface AvatarProps {
  displayName: string;
  color: string;
  size?: number;
}

export function Avatar({ displayName, color, size = 48 }: AvatarProps) {
  const initial = displayName.trim().charAt(0).toUpperCase() || "?";

  return (
    <span
      aria-hidden="true"
      style={{ backgroundColor: color, width: size, height: size, fontSize: size * 0.44 }}
      className="flex shrink-0 items-center justify-center rounded-full font-extrabold text-snow"
    >
      {initial}
    </span>
  );
}
