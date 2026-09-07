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
 * The wind is a sine of the node's position *along the whole path*, not within
 * its unit -- otherwise the pattern visibly restarts at every unit header and
 * the trail reads as three separate columns.
 *
 * The amplitude is `min(26vw, 120px)`: a fixed pixel sway on desktop, falling
 * back to a fraction of the viewport at 375px so a node can never be pushed off
 * the edge. A percentage of the node's own width (its default meaning here)
 * would have given a sway of ~20px, which is not a wind at all.
 */

const WIND_AMPLITUDE = "min(26vw, 120px)";
const WIND_FREQUENCY = 0.8;

interface SkillPathProps {
  path: CoursePath;
  userId: number;
}

export function SkillPath({ path, userId }: SkillPathProps) {
  const router = useRouter();
  const [selected, setSelected] = useState<Skill | null>(null);
  const [isStarting, setIsStarting] = useState(false);

  const allSkills = path.units.flatMap((unit) => unit.skills);

  // The single node that gets the START bubble: the first one the learner can
  // actually play. Computed across the flattened path so only one ever shows.
  const activeSkillId = allSkills.find(
    (skill) => skill.state === "available" || skill.state === "in_progress",
  )?.id;

  // Position along the whole trail, so the sine keeps running across units.
  const pathIndex = new Map(allSkills.map((skill, index) => [skill.id, index]));

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
            {unit.skills.map((skill) => (
              <div
                key={skill.id}
                className="relative transition-transform"
                style={{
                  transform: `translateX(calc(${Math.sin(
                    (pathIndex.get(skill.id) ?? 0) * WIND_FREQUENCY,
                  ).toFixed(3)} * ${WIND_AMPLITUDE}))`,
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
