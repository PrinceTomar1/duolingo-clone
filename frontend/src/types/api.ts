/**
 * TypeScript mirrors of the backend's Pydantic response models.
 *
 * These are hand-written rather than generated so every field is something I
 * can explain, and so the compiler catches a rename on either side the moment
 * `api.ts` stops type-checking.
 */

export type ExerciseType =
  | "MULTIPLE_CHOICE"
  | "TRANSLATE_WORD_BANK"
  | "MATCH_PAIRS"
  | "FILL_BLANK"
  | "TYPE_ANSWER";

export type SkillState = "locked" | "available" | "in_progress" | "completed";

export interface Skill {
  id: number;
  order_index: number;
  title: string;
  icon: string;
  lesson_count: number;
  crowns: number;
  state: SkillState;
  required_crowns_to_unlock: number;
}

export interface Unit {
  id: number;
  order_index: number;
  title: string;
  description: string;
  color_hex: string;
  skills: Skill[];
}

export interface CoursePath {
  course_id: number;
  title: string;
  from_language: string;
  to_language: string;
  units: Unit[];
  total_crowns: number;
}

/** One row of the language picker. */
export interface CourseSummary {
  id: number;
  title: string;
  from_language: string;
  to_language: string;
}

/**
 * The per-type shape of `Exercise.payload`.
 *
 * A discriminated union keyed on `type` is what lets the lesson player switch
 * on the exercise and have the compiler narrow the payload for it -- no casts,
 * no `any`, and a missing case is a build error.
 */
export interface MultipleChoicePayload {
  question: string;
  options: string[];
}

export interface WordBankPayload {
  source_sentence: string;
  word_bank: string[];
}

export interface MatchPairsPayload {
  left: string[];
  right: string[];
}

export interface FillBlankPayload {
  sentence: string;
  options: string[];
  translation: string;
}

export interface TypeAnswerPayload {
  source_sentence: string;
}

interface ExerciseBase {
  id: number;
  order_index: number;
  prompt: string;
  audio_url: string | null;
}

export type Exercise =
  | (ExerciseBase & { type: "MULTIPLE_CHOICE"; payload: MultipleChoicePayload })
  | (ExerciseBase & { type: "TRANSLATE_WORD_BANK"; payload: WordBankPayload })
  | (ExerciseBase & { type: "MATCH_PAIRS"; payload: MatchPairsPayload })
  | (ExerciseBase & { type: "FILL_BLANK"; payload: FillBlankPayload })
  | (ExerciseBase & { type: "TYPE_ANSWER"; payload: TypeAnswerPayload });

export interface Lesson {
  id: number;
  skill_id: number;
  order_index: number;
  xp_reward: number;
  skill_title: string;
  exercises: Exercise[];
}

/** The answer envelope posted back for each exercise type. */
export type SubmittedAnswer =
  | { choice: string }
  | { words: string[] }
  | { text: string }
  | { pairs: Array<{ left: string; right: string }> };

export interface StartAttempt {
  attempt_id: number;
  lesson_id: number;
  hearts_remaining: number;
}

export interface AnswerResult {
  is_correct: boolean;
  correct_answer: string;
  explanation: string | null;
  hearts_remaining: number;
  attempt_failed: boolean;
}

export interface UnlockedAchievement {
  code: string;
  title: string;
  description: string;
  icon: string;
  color_hex: string;
}

export interface CompletionSummary {
  attempt_id: number;
  xp_earned: number;
  total_xp: number;
  accuracy_percent: number;
  duration_seconds: number;
  is_perfect: boolean;
  crown_earned: boolean;
  skill_crowns: number;
  skill_completed: boolean;
  current_streak: number;
  streak_extended: boolean;
  daily_goal_xp: number;
  daily_xp_earned: number;
  hearts_remaining: number;
  gems: number;
  unlocked_achievements: UnlockedAchievement[];
}

export interface User {
  id: number;
  username: string;
  display_name: string;
  avatar_color: string;
  /** Whether switching into this learner needs a password prompt. Never the hash itself. */
  has_password: boolean;
  created_at: string;
}

export interface UserStats {
  user_id: number;
  total_xp: number;
  current_streak: number;
  longest_streak: number;
  last_active_date: string | null;
  hearts: number;
  max_hearts: number;
  seconds_until_next_heart: number | null;
  gems: number;
  /** Server-owned price of a refill. Never hardcode this in the UI. */
  heart_refill_gem_cost: number;
  daily_goal_xp: number;
  daily_xp_earned: number;
  weekly_xp: number;
}

export interface Achievement {
  code: string;
  title: string;
  description: string;
  icon: string;
  color_hex: string;
  target: number;
  progress: number;
  unlocked_at: string | null;
}

export interface DailyXp {
  date: string;
  xp_earned: number;
}

export interface UserProfile {
  user: User;
  stats: UserStats;
  total_crowns: number;
  lessons_completed: number;
  achievements: Achievement[];
  recent_activity: DailyXp[];
}

export interface LeaderboardEntry {
  rank: number;
  user_id: number;
  username: string;
  display_name: string;
  avatar_color: string;
  weekly_xp: number;
  total_xp: number;
  current_streak: number;
  has_password: boolean;
}

export interface Leaderboard {
  week_start: string;
  week_end: string;
  entries: LeaderboardEntry[];
}
