/**
 * The only module in the app that talks to the network.
 *
 * Every call goes through `request`, so the error shape and the base URL are
 * decided once. The base URL comes from `NEXT_PUBLIC_API_URL`; local dev sets
 * it explicitly (see .env.example) to the backend's own address. Left unset,
 * it defaults to same-origin ("") rather than a hardcoded host -- that is what
 * lets the deployed app sit behind next.config.mjs's rewrite of `/api/v1/*` to
 * the real backend, so the whole product is reachable from one URL with no
 * separate backend link to hand out.
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

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "";

/**
 * An error carrying the backend's status code and error *type*.
 *
 * `code` mirrors the `error` field the API sends with every domain failure
 * ("OutOfHeartsError", "SkillLockedError", ...). Callers branch on it instead of
 * matching message text, so a reworded message never silently changes which
 * screen a learner is shown.
 */
export class ApiError extends Error {
  readonly status: number;
  readonly code: string | null;

  constructor(status: number, message: string, code: string | null = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

interface RequestOptions {
  method?: "GET" | "POST";
  body?: unknown;
  /** Path screens must not serve a cached path after a lesson changes it. */
  cache?: RequestCache;
}

/** One entry of FastAPI's 422 body: which field failed, and why. */
interface ValidationIssue {
  loc?: (string | number)[];
  msg?: string;
}

/**
 * Turn any error body into one line a human can read.
 *
 * The API answers with `detail` in two different shapes. Our own domain errors
 * send a string ("Finish the previous skill..."), but FastAPI's request
 * validation sends an *array* of per-field objects. Reading `.detail` blindly
 * put that array into an Error, which rendered to the learner as
 * "[object Object]" -- so each shape is handled explicitly here.
 */
function errorMessage(payload: unknown, status: number): string {
  const fallback = `Request failed (${status})`;
  if (typeof payload !== "object" || payload === null) return fallback;

  const detail = (payload as { detail?: unknown }).detail;
  if (typeof detail === "string" && detail.trim() !== "") return detail;

  if (Array.isArray(detail)) {
    const issues = (detail as ValidationIssue[])
      .map((issue) => {
        // `loc` is like ["body", "user_id"]; the last hop names the field, and
        // the first is only the request part it came from.
        const field = issue.loc?.slice(1).join(".") ?? "";
        const reason = issue.msg ?? "is invalid";
        return field ? `${field}: ${reason}` : reason;
      })
      .filter(Boolean);
    if (issues.length > 0) return issues.join("; ");
  }

  return fallback;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, cache = "no-store" } = options;

  let response: Response;
  try {
    response = await fetch(`${BASE_URL}/api/v1${path}`, {
      method,
      cache,
      headers: body === undefined ? undefined : { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    // `fetch` rejects with a bare TypeError ("Failed to fetch") when the API is
    // unreachable. Translated here so every caller can render `error.message`
    // directly instead of showing the learner a browser internal.
    throw new ApiError(0, "Can't reach the server. Check your connection and try again.");
  }

  if (!response.ok) {
    const payload = await response.json().catch(() => undefined);
    const code =
      typeof payload === "object" && payload !== null && typeof (payload as { error?: unknown }).error === "string"
        ? ((payload as { error: string }).error)
        : null;
    throw new ApiError(response.status, errorMessage(payload, response.status), code);
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
