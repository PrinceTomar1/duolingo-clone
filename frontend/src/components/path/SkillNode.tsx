"use client";

import { motion } from "framer-motion";

import { Icon } from "@/components/ui/Icon";
import { ProgressRing } from "@/components/ui/ProgressRing";
import { clsx } from "@/lib/clsx";
import type { Skill } from "@/types/api";

/**
 * One circular node on the path.
 *
 * The 3D look is the same trick as the button: a `border-b-[6px]` in the
 * shadow colour reads as the disc's side wall, and pressing collapses it while
 * translating down by the same amount.
 */

const NODE_SIZE = 72;

interface SkillNodeProps {
  skill: Skill;
  /** Colour of the owning unit, so a node matches its section header. */
  unitColor: string;
  isActive: boolean;
  onSelect: (skill: Skill) => void;
}

export function SkillNode({ skill, unitColor, isActive, onSelect }: SkillNodeProps) {
  const isLocked = skill.state === "locked";
  const isComplete = skill.state === "completed";

  return (
    <div className="relative flex flex-col items-center">
      {isActive && <StartBubble />}

      {/* The crown ring sits outside the disc, so it needs room around it. */}
      <div className="relative" style={{ width: NODE_SIZE + 16, height: NODE_SIZE + 16 }}>
        <ProgressRing
          progress={skill.lesson_count > 0 ? skill.crowns / skill.lesson_count : 0}
          size={NODE_SIZE + 16}
          strokeWidth={5}
          color={isComplete ? "#FFC800" : unitColor}
          trackColor="#E5E5E5"
          className="absolute inset-0"
        />

        <button
          type="button"
          onClick={() => onSelect(skill)}
          disabled={isLocked}
          aria-label={`${skill.title} — ${skill.state.replace("_", " ")}, ${skill.crowns} of ${skill.lesson_count} crowns`}
          style={
            isLocked
              ? undefined
              : { backgroundColor: isComplete ? "#FFC800" : unitColor, borderBottomColor: shade(isComplete ? "#FFC800" : unitColor) }
          }
          className={clsx(
            "absolute left-2 top-2 flex items-center justify-center rounded-full border-b-[6px] transition-all duration-100",
            isLocked
              ? "cursor-not-allowed border-hare bg-swan text-hare dark:border-night-border dark:bg-night-raised dark:text-wolf"
              : "text-snow active:translate-y-1.5 active:border-b-0",
          )}
        >
          <span style={{ width: NODE_SIZE, height: NODE_SIZE }} className="flex items-center justify-center">
            <Icon name={isLocked ? "lock" : skill.icon} size={34} strokeWidth={2.5} />
          </span>
        </button>
      </div>

      <p
        className={clsx(
          "mt-1 max-w-[8rem] text-center text-xs font-extrabold",
          isLocked ? "text-hare" : "text-eel dark:text-swan",
        )}
      >
        {skill.title}
      </p>
    </div>
  );
}

/** The bouncing "START" speech bubble above the one node to play next. */
function StartBubble() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      className="absolute -top-11 z-10 animate-bubble-bounce"
    >
      <div className="relative rounded-2xl border-2 border-swan bg-snow px-4 py-1.5 text-sm font-extrabold uppercase tracking-wide text-feather dark:border-night-border dark:bg-night-raised">
        Start
        {/* The tail: a rotated square with two borders, half-covered by the
            bubble's own background so only the outer two edges show. */}
        <span className="absolute -bottom-[7px] left-1/2 h-3 w-3 -translate-x-1/2 rotate-45 border-b-2 border-r-2 border-swan bg-snow dark:border-night-border dark:bg-night-raised" />
      </div>
    </motion.div>
  );
}

/** Darken a hex colour for the node's under-shadow. */
function shade(hex: string): string {
  const value = parseInt(hex.slice(1), 16);
  const darken = (channel: number) => Math.round(channel * 0.78);
  const r = darken((value >> 16) & 255);
  const g = darken((value >> 8) & 255);
  const b = darken(value & 255);
  return `#${((r << 16) | (g << 8) | b).toString(16).padStart(6, "0")}`;
}
