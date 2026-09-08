"use client";

import { useEffect, useState } from "react";

import { AchievementCard } from "@/components/profile/AchievementCard";
import { ActivityChart } from "@/components/profile/ActivityChart";
import { Avatar } from "@/components/ui/Avatar";
import { Button } from "@/components/ui/Button";
import { ErrorNotice } from "@/components/ui/ErrorNotice";
import { Icon } from "@/components/ui/Icon";
import { PageHeader } from "@/components/ui/PageHeader";
import { api, ApiError } from "@/lib/api";
import type { IconName } from "@/lib/icon-paths";
import { formatNumber } from "@/lib/format";
import { useSessionStore } from "@/store/useSessionStore";
import type { LeaderboardEntry, UserProfile } from "@/types/api";

/** Identity, headline stats, badges and the activity ledger. */
export default function ProfilePage() {
  const user = useSessionStore((state) => state.user);
  const switchTo = useSessionStore((state) => state.switchTo);
  const createLearner = useSessionStore((state) => state.createLearner);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [learners, setLearners] = useState<LeaderboardEntry[]>([]);
  const [switcherOpen, setSwitcherOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [newUsername, setNewUsername] = useState("");
  const [newDisplayName, setNewDisplayName] = useState("");
  const [createError, setCreateError] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);

  useEffect(() => {
    if (!user) return;
    api
      .profile(user.id)
      .then(setProfile)
      .catch((cause: unknown) =>
        setError(cause instanceof Error ? cause.message : "Could not load your profile"),
      );
  }, [user]);

  // Loaded once, lazily, only if the switcher is actually opened -- most
  // visits to this page never need the full learner list.
  useEffect(() => {
    if (!switcherOpen || learners.length > 0) return;
    api.leaderboard().then((board) => setLearners(board.entries));
  }, [switcherOpen, learners.length]);

  async function handleCreateLearner(event: React.FormEvent) {
    event.preventDefault();
    setIsCreating(true);
    setCreateError(null);
    try {
      await createLearner(newUsername.trim(), newDisplayName.trim());
      setSwitcherOpen(false);
      setCreating(false);
      setNewUsername("");
      setNewDisplayName("");
    } catch (cause) {
      setCreateError(cause instanceof ApiError ? cause.message : "Could not create that learner");
    } finally {
      setIsCreating(false);
    }
  }

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

      <section className="mb-4 flex items-center gap-4">
        <Avatar displayName={profile.user.display_name} color={profile.user.avatar_color} size={80} />
        <div className="min-w-0 flex-1">
          <h2 className="truncate text-xl font-extrabold">{profile.user.display_name}</h2>
          <p className="text-sm font-bold text-wolf">@{profile.user.username}</p>
          <p className="text-xs font-bold text-hare">Joined {joined}</p>
        </div>
        <button
          type="button"
          onClick={() => setSwitcherOpen((open) => !open)}
          aria-expanded={switcherOpen}
          className="flex shrink-0 items-center gap-1.5 rounded-xl border-2 border-swan px-3 py-2 text-xs font-extrabold uppercase tracking-wide text-wolf transition-colors hover:bg-polar dark:border-night-border dark:hover:bg-night-raised"
        >
          <Icon name="users" size={16} />
          Switch learner
        </button>
      </section>

      {/* There is no real login in this build (see the assignment's own note
          on simplified auth), so there is nothing to log out *of* -- every
          seeded learner is an equally valid demo account. This is the honest
          equivalent: pick a different one rather than pretending to end a
          session that was never started. */}
      {switcherOpen && (
        <section className="mb-8 rounded-2xl border-2 border-swan p-3 dark:border-night-border">
          <p className="mb-2 px-1 text-xs font-bold text-hare">
            No real accounts here — pick any seeded learner to view their progress, or add a new one.
          </p>
          {learners.length === 0 ? (
            <p className="px-1 py-2 text-sm font-bold text-wolf">Loading learners…</p>
          ) : (
            <ul className="space-y-1">
              {learners.map((learner) => (
                <li key={learner.user_id}>
                  <button
                    type="button"
                    onClick={() => {
                      setSwitcherOpen(false);
                      void switchTo(learner.username);
                    }}
                    disabled={learner.username === profile.user.username}
                    className="flex w-full items-center gap-3 rounded-xl px-2 py-2 text-left transition-colors hover:bg-polar disabled:cursor-default disabled:opacity-50 disabled:hover:bg-transparent dark:hover:bg-night-raised"
                  >
                    <Avatar displayName={learner.display_name} color={learner.avatar_color} size={32} />
                    <span className="min-w-0 flex-1 truncate text-sm font-bold">
                      {learner.display_name}
                      {learner.username === profile.user.username && " (current)"}
                    </span>
                    <span className="shrink-0 text-xs font-bold text-wolf">
                      {formatNumber(learner.total_xp)} XP
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}

          <div className="mt-2 border-t-2 border-swan pt-2 dark:border-night-border">
            {!creating ? (
              <button
                type="button"
                onClick={() => setCreating(true)}
                className="flex w-full items-center gap-3 rounded-xl px-2 py-2 text-left text-sm font-extrabold text-macaw transition-colors hover:bg-polar dark:hover:bg-night-raised"
              >
                <Icon name="plus" size={18} />
                Add a new learner
              </button>
            ) : (
              <form onSubmit={handleCreateLearner} className="space-y-2 px-1 py-1">
                <div>
                  <label htmlFor="new-learner-display-name" className="sr-only">
                    Display name
                  </label>
                  <input
                    id="new-learner-display-name"
                    type="text"
                    required
                    maxLength={100}
                    placeholder="Display name"
                    value={newDisplayName}
                    onChange={(event) => setNewDisplayName(event.target.value)}
                    className="w-full rounded-xl border-2 border-swan bg-transparent px-3 py-2 text-sm font-bold outline-none focus:border-macaw dark:border-night-border"
                  />
                </div>
                <div>
                  <label htmlFor="new-learner-username" className="sr-only">
                    Username
                  </label>
                  <input
                    id="new-learner-username"
                    type="text"
                    required
                    minLength={2}
                    maxLength={50}
                    pattern="[a-zA-Z0-9_]+"
                    title="Letters, numbers and underscores only"
                    placeholder="Username"
                    value={newUsername}
                    onChange={(event) => setNewUsername(event.target.value)}
                    className="w-full rounded-xl border-2 border-swan bg-transparent px-3 py-2 text-sm font-bold outline-none focus:border-macaw dark:border-night-border"
                  />
                </div>
                {createError && <p className="px-1 text-xs font-bold text-cardinal">{createError}</p>}
                <div className="flex gap-2 pt-1">
                  <Button type="submit" size="sm" disabled={isCreating}>
                    {isCreating ? "Creating…" : "Create & switch"}
                  </Button>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      setCreating(false);
                      setCreateError(null);
                      setNewUsername("");
                      setNewDisplayName("");
                    }}
                  >
                    Cancel
                  </Button>
                </div>
              </form>
            )}
          </div>
        </section>
      )}

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
