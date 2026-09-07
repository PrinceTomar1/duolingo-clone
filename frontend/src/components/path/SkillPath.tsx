"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { SkillNode } from "@/components/path/SkillNode";
import { UnitHeader } from "@/components/path/UnitHeader";
import { SkillPopover } from "@/components/path/SkillPopover";
import { api } from "@/lib/api";
import type { CoursePath, Skill } from "@/types/api";

/**
 * The winding trail of skill nodes.
 *
 * The wind is a sine of the node's index: `sin(i * 0.9)` gives a smooth
 * left-right sway that never repeats too obviously, scaled to a percentage of
 * the container so it narrows gracefully at 375px instead of pushing a node off
 * the edge.
 */

const WIND_AMPLITUDE_PERCENT = 26;

interface SkillPathProps {
  path: CoursePath;
  userId: number;
}

export function SkillPath({ path, userId }: SkillPathProps) {
  const router = useRouter();
  const [selected, setSelected] = useState<Skill | null>(null);
  const [isStarting, setIsStarting] = useState(false);

  // The single node that gets the START bubble: the first one the learner can
  // actually play. Computed across the flattened path so only one ever shows.
  const activeSkillId = path.units
    .flatMap((unit) => unit.skills)
    .find((skill) => skill.state === "available" || skill.state === "in_progress")?.id;

  async function startSkill(skill: Skill): Promise<void> {
    setIsStarting(true);
    try {
      const lessonIds = await api.skillLessonIds(skill.id);
      // Crowns count completed lessons, so the next unplayed lesson is at that
      // index -- and once the skill is finished we replay its last lesson.
      const next = lessonIds[Math.min(skill.crowns, lessonIds.length - 1)];
      if (next !== undefined) router.push(`/lesson/${next}?userId=${userId}`);
    } finally {
      setIsStarting(false);
    }
  }

  return (
    <div className="pb-10">
      {path.units.map((unit) => (
        <section key={unit.id} aria-label={unit.description}>
          <UnitHeader title={unit.title} description={unit.description} color={unit.color_hex} />

          <div className="flex flex-col items-center gap-6">
            {unit.skills.map((skill, index) => (
              <div
                key={skill.id}
                className="relative"
                style={{
                  transform: `translateX(${Math.sin(index * 0.9) * WIND_AMPLITUDE_PERCENT}%)`,
                }}
              >
                <SkillNode
                  skill={skill}
                  unitColor={unit.color_hex}
                  isActive={skill.id === activeSkillId}
                  onSelect={setSelected}
                />
              </div>
            ))}
          </div>
        </section>
      ))}

      {selected && (
        <SkillPopover
          skill={selected}
          isStarting={isStarting}
          onStart={() => void startSkill(selected)}
          onClose={() => setSelected(null)}
        />
      )}
    </div>
  );
}
