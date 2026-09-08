"use client";

import { useEffect, useState } from "react";

import { SkillPath } from "@/components/path/SkillPath";
import { PathSkeleton } from "@/components/path/PathSkeleton";
import { Icon } from "@/components/ui/Icon";
import { ErrorNotice } from "@/components/ui/ErrorNotice";
import { api } from "@/lib/api";
import { useSessionStore } from "@/store/useSessionStore";
import type { CoursePath } from "@/types/api";

/**
 * Courses a real course picker would list. Only Spanish has content behind
 * it -- the brief is explicit that one seeded language is enough -- so the
 * rest are shown, honestly, as not-yet-built rather than left off entirely.
 * A learner opening this should see a deliberate choice, not wonder whether
 * more languages exist and the app just failed to load them.
 */
const OTHER_COURSES = ["French", "German", "Japanese", "Italian"];

/**
 * The Learn screen.
 *
 * A client component because the path is per-learner and must refetch whenever
 * a lesson changes it -- server rendering it would hand back a cached path with
 * stale crowns the moment the learner came back from a lesson.
 */
export default function LearnPage() {
  const user = useSessionStore((state) => state.user);
  const sessionError = useSessionStore((state) => state.error);
  const [path, setPath] = useState<CoursePath | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pickerOpen, setPickerOpen] = useState(false);

  useEffect(() => {
    if (!user) return;
    api
      .coursePath(user.id)
      .then(setPath)
      .catch((cause: unknown) =>
        setError(cause instanceof Error ? cause.message : "Could not load the course"),
      );
  }, [user]);

  if (sessionError ?? error) return <ErrorNotice message={sessionError ?? error ?? ""} />;
  if (!user || !path) return <PathSkeleton />;

  return (
    <>
      <header className="mb-6 flex items-baseline justify-between">
        <h1 className="text-2xl font-extrabold">{path.title}</h1>
        <div className="relative">
          <button
            type="button"
            onClick={() => setPickerOpen((open) => !open)}
            aria-expanded={pickerOpen}
            className="flex items-center gap-1.5 rounded-xl px-2 py-1 text-sm font-bold text-wolf transition-colors hover:bg-polar dark:hover:bg-night-raised"
          >
            {path.from_language} → {path.to_language}
            <Icon name="chevron-down" size={16} />
          </button>
          {pickerOpen && (
            <ul className="absolute right-0 top-full z-20 mt-1 w-48 rounded-2xl border-2 border-swan bg-snow p-2 shadow-lg dark:border-night-border dark:bg-night-raised">
              <li>
                <span className="flex items-center justify-between rounded-xl bg-macaw/10 px-3 py-2 text-sm font-extrabold text-macaw">
                  {path.to_language}
                  <Icon name="check" size={16} />
                </span>
              </li>
              {OTHER_COURSES.map((language) => (
                <li key={language}>
                  <span className="flex items-center justify-between px-3 py-2 text-sm font-bold text-hare">
                    {language}
                    <span className="text-xs uppercase tracking-wide">Coming soon</span>
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </header>
      <SkillPath path={path} userId={user.id} />
    </>
  );
}
