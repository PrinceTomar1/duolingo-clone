"use client";

/**
 * All state for one run through a lesson.
 *
 * A store rather than component state because the header (progress, hearts),
 * the exercise and the feedback bar are siblings that all read the same run --
 * threading it through props would mean the player passing eight values down
 * two levels.
 *
 * Note what is *not* here: whether an answer is correct. The client never
 * decides that; it posts the answer and renders whatever the server returns.
 */

import { create } from "zustand";

import { ApiError, api } from "@/lib/api";
import { playCorrect, playIncorrect } from "@/lib/sound";
import type { AnswerResult, CompletionSummary, Lesson, SubmittedAnswer } from "@/types/api";

export type LessonStatus = "loading" | "playing" | "checked" | "failed" | "complete" | "error";

interface LessonState {
  lesson: Lesson | null;
  attemptId: number | null;
  index: number;
  /** The answer in progress. `null` means CHECK stays disabled. */
  draft: SubmittedAnswer | null;
  result: AnswerResult | null;
  hearts: number;
  maxHearts: number;
  mistakes: number;
  status: LessonStatus;
  summary: CompletionSummary | null;
  errorMessage: string | null;
  /** HTTP status behind `errorMessage`; 0 means the request never landed. */
  errorStatus: number | null;

  load: (lessonId: number, userId: number) => Promise<void>;
  setDraft: (draft: SubmittedAnswer | null) => void;
  check: () => Promise<void>;
  advance: () => Promise<void>;
  reset: () => void;
}

const INITIAL = {
  lesson: null,
  attemptId: null,
  index: 0,
  draft: null,
  result: null,
  hearts: 5,
  maxHearts: 5,
  mistakes: 0,
  status: "loading" as LessonStatus,
  summary: null,
  errorMessage: null,
  errorStatus: null,
};

export const useLessonStore = create<LessonState>((set, get) => ({
  ...INITIAL,

  load: async (lessonId, userId) => {
    set({ ...INITIAL });
    try {
      // The attempt is opened first: if the skill is locked or hearts are
      // empty, the server refuses here and no exercise is ever shown.
      const attempt = await api.startAttempt(lessonId, userId);
      // The bar size is a server rule (MAX_HEARTS), so it is read rather than
      // assumed; hardcoding 5 drew a five-heart bar on a three-heart server.
      const [lesson, stats] = await Promise.all([
        api.lesson(lessonId),
        api.stats(userId),
      ]);
      set({
        lesson,
        attemptId: attempt.attempt_id,
        hearts: attempt.hearts_remaining,
        maxHearts: stats.max_hearts,
        status: attempt.hearts_remaining > 0 ? "playing" : "failed",
      });
    } catch (cause) {
      // Being out of hearts is not a breakage -- it is a state the game has a
      // screen for. Routing it to the generic error notice dead-ended the
      // learner with "Back to the path" and no way to spend gems or see when
      // the next heart lands, so it is mapped to the same `failed` state that
      // running dry mid-lesson produces.
      if (cause instanceof ApiError && cause.code === "OutOfHeartsError") {
        set({ status: "failed", hearts: 0 });
        return;
      }
      set({
        status: "error",
        errorMessage: cause instanceof Error ? cause.message : "Could not start this lesson",
        errorStatus: cause instanceof ApiError ? cause.status : null,
      });
    }
  },

  setDraft: (draft) => set({ draft }),

  check: async () => {
    const { attemptId, lesson, index, draft } = get();
    const exercise = lesson?.exercises[index];
    if (!attemptId || !exercise || !draft) return;

    const result = await api.submitAnswer(attemptId, exercise.id, draft);
    if (result.is_correct) playCorrect();
    else playIncorrect();

    set((state) => ({
      result,
      hearts: result.hearts_remaining,
      mistakes: state.mistakes + (result.is_correct ? 0 : 1),
      // A failed attempt still shows its feedback bar; the out-of-hearts modal
      // is raised by the player once the learner dismisses it.
      status: "checked",
    }));
  },

  advance: async () => {
    const { lesson, index, attemptId, result } = get();
    if (!lesson || !attemptId) return;

    if (result?.attempt_failed) {
      set({ status: "failed" });
      return;
    }

    if (index + 1 < lesson.exercises.length) {
      set({ index: index + 1, draft: null, result: null, status: "playing" });
      return;
    }

    const summary = await api.completeAttempt(attemptId);
    set({ summary, status: "complete" });
  },

  reset: () => set({ ...INITIAL }),
}));
