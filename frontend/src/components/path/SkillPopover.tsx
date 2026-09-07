"use client";

import { motion } from "framer-motion";

import { Button } from "@/components/ui/Button";
import { Icon } from "@/components/ui/Icon";
import type { Skill } from "@/types/api";

/**
 * The sheet that opens when a node is tapped.
 *
 * Duolingo shows a small popover anchored to the node on desktop and a bottom
 * sheet on mobile; this is the bottom sheet, which works at every width and
 * needs no positioning maths against a scrolling trail.
 */
interface SkillPopoverProps {
  skill: Skill;
  isStarting: boolean;
  onStart: () => void;
  onClose: () => void;
}

export function SkillPopover({ skill, isStarting, onStart, onClose }: SkillPopoverProps) {
  const isComplete = skill.state === "completed";
  const lessonNumber = Math.min(skill.crowns + 1, skill.lesson_count);

  return (
    <div className="fixed inset-0 z-40 flex items-end justify-center" role="dialog" aria-modal="true">
      <button
        type="button"
        aria-label="Close"
        onClick={onClose}
        className="absolute inset-0 bg-black/40"
      />

      <motion.div
        initial={{ y: 120 }}
        animate={{ y: 0 }}
        transition={{ type: "spring", stiffness: 400, damping: 34 }}
        className="relative w-full max-w-md rounded-t-3xl border-t-2 border-swan bg-snow p-5 pb-8 dark:border-night-border dark:bg-night-raised"
      >
        <div className="mb-4 flex items-center gap-3">
          <Icon name={skill.icon} size={32} className="text-feather" strokeWidth={2.5} />
          <div>
            <h3 className="text-lg font-extrabold">{skill.title}</h3>
            <p className="flex items-center gap-1 text-sm font-bold text-wolf">
              <Icon name="crown" size={16} className="text-bee" />
              {skill.crowns} / {skill.lesson_count} crowns
            </p>
          </div>
        </div>

        <Button variant={isComplete ? "secondary" : "primary"} size="lg" fullWidth onClick={onStart} disabled={isStarting}>
          {isStarting
            ? "Loading…"
            : isComplete
              ? "Practice again"
              : `Start lesson ${lessonNumber}`}
        </Button>
      </motion.div>
    </div>
  );
}
