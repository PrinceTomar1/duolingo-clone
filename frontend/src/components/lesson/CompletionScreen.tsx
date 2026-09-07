"use client";

import { useRouter } from "next/navigation";

import { Confetti } from "@/components/lesson/Confetti";
import { Button } from "@/components/ui/Button";
import { Icon } from "@/components/ui/Icon";
import type { IconName } from "@/lib/icon-paths";
import { formatDuration } from "@/lib/format";
import type { CompletionSummary } from "@/types/api";

/**
 * The "Lesson Complete!" screen.
 *
 * The three outlined stat cards are Duolingo's: total XP in Bee yellow,
 * time in Macaw blue, accuracy in Feather green. Each is a coloured border with
 * a solid header strip, which is what makes them read as trophies rather than
 * table cells.
 */
interface CompletionScreenProps {
  summary: CompletionSummary;
  onContinue: () => void;
}

export function CompletionScreen({ summary, onContinue }: CompletionScreenProps) {
  const router = useRouter();

  return (
    <div className="relative flex min-h-screen flex-col items-center justify-center px-5 py-10 text-center">
      <Confetti />

      <div className="relative z-10 w-full max-w-lg">
        <Icon name="trophy" size={96} className="mx-auto mb-4 text-bee" strokeWidth={1.75} />
        <h1 className="text-3xl font-extrabold text-bee sm:text-4xl">Lesson Complete!</h1>
        <p className="mt-2 text-sm font-bold text-wolf">
          {summary.crown_earned
            ? summary.skill_completed
              ? "Skill finished — the next one is unlocked."
              : "You earned a crown for this lesson."
            : "Practice counts too — XP banked."}
        </p>

        <div className="my-8 grid grid-cols-3 gap-3">
          <StatCard label="Total XP" value={`${summary.xp_earned}`} color="#FFC800" icon="bolt" />
          <StatCard
            label={summary.duration_seconds < 120 ? "Speedy" : "Committed"}
            value={formatDuration(summary.duration_seconds)}
            color="#1CB0F6"
            icon="clock"
          />
          <StatCard
            label={summary.accuracy_percent >= 90 ? "Amazing" : "Good"}
            value={`${summary.accuracy_percent}%`}
            color="#58CC02"
            icon="target"
          />
        </div>

        {summary.streak_extended && (
          <p className="mb-4 flex items-center justify-center gap-2 text-base font-extrabold text-fox">
            <Icon name="flame" size={24} />
            {summary.current_streak} day streak!
          </p>
        )}

        {summary.unlocked_achievements.map((achievement) => (
          <p
            key={achievement.code}
            className="mb-2 flex items-center justify-center gap-2 text-sm font-extrabold"
            style={{ color: achievement.color_hex }}
          >
            <Icon name={achievement.icon} size={20} />
            Achievement unlocked — {achievement.title}
          </p>
        ))}

        <div className="mt-6 flex flex-col gap-3">
          <Button variant="primary" size="lg" fullWidth onClick={onContinue}>
            Continue
          </Button>
          <Button variant="ghost" size="lg" fullWidth onClick={() => router.push("/profile")}>
            View profile
          </Button>
        </div>
      </div>
    </div>
  );
}

interface StatCardProps {
  label: string;
  value: string;
  color: string;
  icon: IconName;
}

function StatCard({ label, value, color, icon }: StatCardProps) {
  return (
    <div className="overflow-hidden rounded-2xl border-2" style={{ borderColor: color }}>
      <p className="py-1 text-xs font-extrabold uppercase tracking-wide text-snow" style={{ backgroundColor: color }}>
        {label}
      </p>
      <p className="flex items-center justify-center gap-1 py-2.5 text-lg font-extrabold" style={{ color }}>
        <Icon name={icon} size={18} />
        {value}
      </p>
    </div>
  );
}
