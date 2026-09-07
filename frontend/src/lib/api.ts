/**
 * The only module in the app that talks to the network.
 *
 * Every call goes through `request`, so retries, error shape and the base URL
 * are decided once. The base URL comes from `NEXT_PUBLIC_API_URL` -- there is
 * no hardcoded localhost anywhere, which is what makes the Vercel build work
 * against a deployed backend without a code change.
 */

import type {
  CoursePath,
  CompletionSummary,
  AnswerResult,
  Leaderboard,
  Lesson,
  StartAttempt,
  SubmittedAnswer,
  User,
  UserProfile,
  UserStats,
} from "@/types/api";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

/** An error carrying the backend's status code so callers can branch on it. */
export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

interface RequestOptions {
  method?: "GET" | "POST";
  body?: unknown;
  /** Path screens must not serve a cached path after a lesson changes it. */
  cache?: RequestCache;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, cache = "no-store" } = options;

  const response = await fetch(`${BASE_URL}/api/v1${path}`, {
    method,
    cache,
    headers: body === undefined ? undefined : { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });

  if (!response.ok) {
    // FastAPI returns `{detail}` for both our domain errors and validation
    // failures, so one shape covers every failure path.
    const detail = await response
      .json()
      .then((payload: { detail?: string }) => payload.detail)
      .catch(() => undefined);
    throw new ApiError(response.status, detail ?? `Request failed (${response.status})`);
  }

  return (await response.json()) as T;
}

export const api = {
  coursePath: (userId: number) => request<CoursePath>(`/course/path?user_id=${userId}`),

  skillLessonIds: (skillId: number) => request<number[]>(`/course/skills/${skillId}/lessons`),

  lesson: (lessonId: number) => request<Lesson>(`/lessons/${lessonId}`),

  startAttempt: (lessonId: number, userId: number) =>
    request<StartAttempt>(`/lessons/${lessonId}/start`, {
      method: "POST",
      body: { user_id: userId },
    }),

  submitAnswer: (attemptId: number, exerciseId: number, answer: SubmittedAnswer) =>
    request<AnswerResult>(`/attempts/${attemptId}/answer`, {
      method: "POST",
      body: { exercise_id: exerciseId, answer },
    }),

  /** Verify one match-pairs link. Deliberately returns a single bit. */
  checkMatchPair: (attemptId: number, exerciseId: number, left: string, right: string) =>
    request<{ is_correct: boolean }>(`/attempts/${attemptId}/match-pair`, {
      method: "POST",
      body: { exercise_id: exerciseId, left, right },
    }),

  completeAttempt: (attemptId: number) =>
    request<CompletionSummary>(`/attempts/${attemptId}/complete`, { method: "POST" }),

  userByUsername: (username: string) => request<User>(`/users/by-username/${username}`),

  stats: (userId: number) => request<UserStats>(`/users/${userId}/stats`),

  profile: (userId: number) => request<UserProfile>(`/users/${userId}/profile`),

  refillHearts: (userId: number) =>
    request<UserStats>(`/users/${userId}/hearts/refill`, { method: "POST" }),

  leaderboard: () => request<Leaderboard>("/leaderboard"),

  advanceDay: (days: number) =>
    request<{ simulated_today: string; streaks: Record<string, number> }>("/dev/advance-day", {
      method: "POST",
      body: { days },
    }),
};
