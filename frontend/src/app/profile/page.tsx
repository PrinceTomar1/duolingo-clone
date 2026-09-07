"use client";

import { useEffect, useState } from "react";

import { AchievementCard } from "@/components/profile/AchievementCard";
import { ActivityChart } from "@/components/profile/ActivityChart";
import { Avatar } from "@/components/ui/Avatar";
import { ErrorNotice } from "@/components/ui/ErrorNotice";
import { Icon } from "@/components/ui/Icon";
import { PageHeader } from "@/components/ui/PageHeader";
import { api } from "@/lib/api";
import type { IconName } from "@/lib/icon-paths";
import { formatNumber } from "@/lib/format";
import { useSessionStore } from "@/store/useSessionStore";
import type { UserProfile } from "@/types/api";

/** Identity, headline stats, badges and the activity ledger. */
export default function ProfilePage() {
  const user = useSessionStore((state) => state.user);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user) return;
    api
      .profile(user.id)
      .then(setProfile)
      .catch((cause: unknown) =>
        setError(cause instanceof Error ? cause.message : "Could not load your profile"),
      );
  }, [user]);

  if (error) return <ErrorNotice message={error} />;
  if (!profile) return <p className="py-10 text-center font-extrabold text-wolf">Loading…</p>;

  const { stats } = profile;
  const joined = new Date(profile.user.created_at).toLocaleDateString("en-US", {
    month: "long",
    year: "numeric",
  });

  return (
    <>
      <PageHeader title="Profile" />

      <section className="mb-8 flex items-center gap-4">
        <Avatar displayName={profile.user.display_name} color={profile.user.avatar_color} size={80} />
        <div className="min-w-0">
          <h2 className="truncate text-xl font-extrabold">{profile.user.display_name}</h2>
          <p className="text-sm font-bold text-wolf">@{profile.user.username}</p>
          <p className="text-xs font-bold text-hare">Joined {joined}</p>
        </div>
      </section>

      <section className="mb-8 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Stat icon="flame" color="#FF9600" value={stats.current_streak} label="Day streak" />
        <Stat icon="bolt" color="#FFC800" value={formatNumber(stats.total_xp)} label="Total XP" />
        <Stat icon="crown" color="#CE82FF" value={profile.total_crowns} label="Crowns" />
        <Stat icon="check" color="#58CC02" value={profile.lessons_completed} label="Lessons" />
      </section>

      <section className="mb-8">
        <h2 className="mb-3 text-lg font-extrabold">XP over the last two weeks</h2>
        <div className="rounded-2xl border-2 border-swan p-4 dark:border-night-border">
          <ActivityChart activity={profile.recent_activity} />
        </div>
      </section>

      <section>
        <h2 className="mb-3 text-lg font-extrabold">
          Achievements{" "}
          <span className="text-sm font-bold text-wolf">
            ({profile.achievements.filter((item) => item.unlocked_at).length} of{" "}
            {profile.achievements.length})
          </span>
        </h2>
        <ul className="space-y-3">
          {profile.achievements.map((achievement) => (
            <AchievementCard key={achievement.code} achievement={achievement} />
          ))}
        </ul>
      </section>
    </>
  );
}

interface StatProps {
  icon: IconName;
  color: string;
  value: string | number;
  label: string;
}

function Stat({ icon, color, value, label }: StatProps) {
  return (
    <div className="flex items-center gap-3 rounded-2xl border-2 border-swan p-3 dark:border-night-border">
      <Icon name={icon} size={28} style={{ color }} />
      <div className="min-w-0">
        <p className="text-lg font-extrabold leading-tight tabular-nums">{value}</p>
        <p className="truncate text-xs font-bold text-wolf">{label}</p>
      </div>
    </div>
  );
}
