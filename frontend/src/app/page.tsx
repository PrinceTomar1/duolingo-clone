"use client";

import { useEffect, useState } from "react";

import { SkillPath } from "@/components/path/SkillPath";
import { PathSkeleton } from "@/components/path/PathSkeleton";
import { ErrorNotice } from "@/components/ui/ErrorNotice";
import { api } from "@/lib/api";
import { useSessionStore } from "@/store/useSessionStore";
import type { CoursePath } from "@/types/api";

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
        <p className="text-sm font-bold text-wolf">
          {path.from_language} → {path.to_language}
        </p>
      </header>
      <SkillPath path={path} userId={user.id} />
    </>
  );
}
