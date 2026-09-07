"use client";

import { useSearchParams } from "next/navigation";

import { LessonPlayer } from "@/components/lesson/LessonPlayer";
import { useSessionStore } from "@/store/useSessionStore";

/**
 * The lesson route.
 *
 * The learner id arrives as a query parameter from the path screen so a shared
 * link still works, but falls back to the bootstrapped session so the route is
 * reachable directly.
 */
export default function LessonPage({ params }: { params: { lessonId: string } }) {
  const searchParams = useSearchParams();
  const sessionUser = useSessionStore((state) => state.user);

  const lessonId = Number(params.lessonId);
  const queryUserId = Number(searchParams.get("userId"));
  const userId = Number.isFinite(queryUserId) && queryUserId > 0 ? queryUserId : sessionUser?.id;

  if (!Number.isFinite(lessonId) || !userId) {
    return <div className="flex min-h-screen items-center justify-center font-extrabold text-wolf">Loading…</div>;
  }

  return <LessonPlayer lessonId={lessonId} userId={userId} />;
}
