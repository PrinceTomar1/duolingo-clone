/**
 * Thin API helpers for the end-to-end specs.
 *
 * The specs read the learner's true server-side numbers so an assertion like
 * "a wrong answer costs a heart" is checked against the database rather than
 * against whatever the page happens to be showing.
 *
 * Note what is *not* here: answer keys. The API withholds them by design, and a
 * browser spec should not be able to reach around that. Lesson grading is
 * covered exhaustively by the backend suite (`backend/tests/test_xp.py` plays
 * real lessons); these specs cover the part only a browser can prove -- that the
 * UI is wired to the server and degrades sanely when it is not.
 */

const API = process.env.E2E_API_URL ?? "http://127.0.0.1:8000";

export interface Stats {
  total_xp: number;
  hearts: number;
  max_hearts: number;
  current_streak: number;
  daily_xp_earned: number;
  daily_goal_xp: number;
  gems: number;
  heart_refill_gem_cost: number;
}

export async function get<T>(path: string): Promise<T> {
  const response = await fetch(`${API}/api/v1${path}`);
  if (!response.ok) throw new Error(`GET ${path} -> ${response.status}`);
  return (await response.json()) as T;
}

export const stats = (userId: number) => get<Stats>(`/users/${userId}/stats`);

export interface SkillNode {
  id: number;
  title: string;
  state: "locked" | "available" | "in_progress" | "completed";
  crowns: number;
  lesson_count: number;
}

export async function skills(userId: number): Promise<SkillNode[]> {
  const path = await get<{ units: { skills: SkillNode[] }[] }>(`/course/path?user_id=${userId}`);
  return path.units.flatMap((unit) => unit.skills);
}

export async function firstLessonOf(skillId: number): Promise<number> {
  const [first] = await get<number[]>(`/course/skills/${skillId}/lessons`);
  if (first === undefined) throw new Error(`skill ${skillId} has no lessons`);
  return first;
}

/** The demo learner the app bootstraps to. */
export const DEMO_USER_ID = 1;

export async function drainHearts(userId: number, lessonId: number): Promise<void> {
  // Spend every heart by answering the same exercise wrongly. Done over the API
  // because the point of the spec is what the *UI* does once the bar is empty.
  for (let guard = 0; guard < 12; guard += 1) {
    const current = await stats(userId);
    if (current.hearts <= 0) return;
    const started = await fetch(`${API}/api/v1/lessons/${lessonId}/start`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId }),
    });
    if (!started.ok) return;
    const { attempt_id: attemptId } = (await started.json()) as { attempt_id: number };
    const lesson = await get<{ exercises: { id: number }[] }>(`/lessons/${lessonId}`);
    await fetch(`${API}/api/v1/attempts/${attemptId}/answer`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ exercise_id: lesson.exercises[0]!.id, answer: { choice: "__wrong__" } }),
    });
  }
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API}/api/v1${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) throw new Error(`POST ${path} -> ${response.status}`);
  return (await response.json()) as T;
}

/**
 * Guarantee the learner can open a lesson.
 *
 * Specs spend hearts, and a drained learner is refused at `start` -- so without
 * this the suite would fail on test *ordering* rather than on behaviour. Rather
 * than reaching into the database, this nudges the app's own simulated clock,
 * which is the mechanism heart regeneration already uses (one heart per 30
 * minutes). Minutes only: advancing whole days would move the streak and change
 * what the other specs are looking at.
 *
 * Requires the backend to be running with DEBUG=true, which mounts /dev.
 */
export async function ensureHearts(minimum = 3): Promise<void> {
  const current = await stats(DEMO_USER_ID);
  if (current.hearts >= minimum) return;
  const missing = minimum - current.hearts;
  await post("/dev/advance-day", { days: 0, minutes: missing * 30 + 5 });
}
