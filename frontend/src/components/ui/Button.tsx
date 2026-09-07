"use client";

import { clsx } from "@/lib/clsx";

/**
 * The Duolingo 3D button.
 *
 * The whole illusion is `border-b-4` in a darker shade of the fill: the border
 * reads as the button's side wall. Pressing removes that border and pushes the
 * element down by exactly the same 4px, so the button appears to physically
 * depress without the layout shifting.
 */

export type ButtonVariant = "primary" | "secondary" | "danger" | "ghost" | "locked";
export type ButtonSize = "sm" | "md" | "lg";

const VARIANTS: Record<ButtonVariant, string> = {
  primary: "bg-feather text-snow border-feather-shadow hover:brightness-105",
  secondary: "bg-macaw text-snow border-macaw-shadow hover:brightness-105",
  danger: "bg-cardinal text-snow border-cardinal-shadow hover:brightness-105",
  // The outlined "skip"/"quit" style: a light face with a grey wall.
  ghost:
    "bg-snow text-wolf border-swan hover:bg-polar dark:bg-night-raised dark:text-hare dark:border-night-border dark:hover:bg-night",
  // Disabled: Swan fill, Hare text, and no wall at all so it never looks tappable.
  locked: "bg-swan text-hare border-swan dark:bg-night-raised dark:text-wolf dark:border-night-raised",
};

const SIZES: Record<ButtonSize, string> = {
  sm: "px-4 py-2 text-xs",
  md: "px-5 py-3 text-sm",
  lg: "px-6 py-3.5 text-base",
};

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  fullWidth?: boolean;
}

export function Button({
  variant = "primary",
  size = "md",
  fullWidth = false,
  className,
  disabled,
  ...props
}: ButtonProps) {
  // A disabled button always renders in the locked style, so a caller can never
  // produce a greyed-out button that still looks pressable.
  const resolved = disabled ? "locked" : variant;

  return (
    <button
      disabled={disabled}
      className={clsx(
        "rounded-2xl border-b-4 font-extrabold uppercase tracking-wide",
        "transition-all duration-100",
        !disabled && "active:translate-y-1 active:border-b-0",
        disabled && "cursor-not-allowed",
        VARIANTS[resolved],
        SIZES[size],
        fullWidth && "w-full",
        className,
      )}
      {...props}
    />
  );
}
