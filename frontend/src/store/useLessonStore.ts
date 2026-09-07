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

import { api } from "@/lib/api";
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
};

export const useLessonStore = create<LessonState>((set, get) => ({
  ...INITIAL,

  load: async (lessonId, userId) => {
    set({ ...INITIAL });
    try {
      // The attempt is opened first: if the skill is locked or hearts are
      // empty, the server refuses here and no exercise is ever shown.
      const attempt = await api.startAttempt(lessonId, userId);
      const lesson = await api.lesson(lessonId);
      set({
        lesson,
        attemptId: attempt.attempt_id,
        hearts: attempt.hearts_remaining,
        status: attempt.hearts_remaining > 0 ? "playing" : "failed",
      });
    } catch (cause) {
      set({
        status: "error",
        errorMessage: cause instanceof Error ? cause.message : "Could not start this lesson",
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
