"use client";

/**
 * The lesson flow, extracted from the player component.
 *
 * The component's job is layout; this hook's job is the sequence — hold the
 * draft, check it, advance, verify a match pair, refill hearts. Splitting them
 * keeps the player readable and makes the flow the thing you review when the
 * flow is what changed.
 *
 * Every decision still belongs to the server: this hook posts and reacts.
 */

import { useCallback, useEffect, useState } from "react";

import { EMPTY_MATCH_STATE } from "@/components/exercises/MatchPairs";
import type { ExerciseDraft } from "@/components/exercises/ExerciseView";
import { api } from "@/lib/api";
import { buildAnswer } from "@/lib/answers";
import { useLessonStore } from "@/store/useLessonStore";
import { useSessionStore } from "@/store/useSessionStore";
import { useToastStore } from "@/store/useToastStore";
import type { CompletionSummary } from "@/types/api";

export const EMPTY_DRAFT: ExerciseDraft = {
  choice: null,
  text: "",
  words: [],
  match: EMPTY_MATCH_STATE,
};

export function useLessonRunner(lessonId: number, userId: number) {
  const store = useLessonStore();
  const refreshStats = useSessionStore((state) => state.refreshStats);
  const pushToast = useToastStore((state) => state.push);

  const [draft, setDraft] = useState<ExerciseDraft>(EMPTY_DRAFT);
  const [isBusy, setIsBusy] = useState(false);

  const { load, reset } = store;
  useEffect(() => {
    void load(lessonId, userId);
    return reset;
  }, [lessonId, userId, load, reset]);

  const exercise = store.lesson?.exercises[store.index];
  const answer = exercise ? buildAnswer(exercise, draft) : null;
  const isLastExercise = store.lesson
    ? store.index === store.lesson.exercises.length - 1
    : false;

  /** Raise the streak and achievement celebrations the summary reports. */
  const celebrate = useCallback(
    (summary: CompletionSummary) => {
      if (summary.streak_extended) {
        pushToast({
          icon: "flame",
          title: `${summary.current_streak} day streak!`,
          detail: "Come back tomorrow to keep it alive.",
          color: "#FF9600",
        });
      }
      for (const achievement of summary.unlocked_achievements) {
        pushToast({
          icon: achievement.icon,
          title: `Achievement unlocked — ${achievement.title}`,
          detail: achievement.description,
          color: achievement.color_hex,
        });
      }
    },
    [pushToast],
  );

  const check = useCallback(async () => {
    if (!answer || isBusy || store.result) return;
    setIsBusy(true);
    try {
      useLessonStore.getState().setDraft(answer);
      await useLessonStore.getState().check();
    } finally {
      setIsBusy(false);
    }
  }, [answer, isBusy, store.result]);

  const advance = useCallback(async () => {
    setIsBusy(true);
    try {
      await useLessonStore.getState().advance();
      const summary = useLessonStore.getState().summary;
      if (summary) celebrate(summary);
      setDraft(EMPTY_DRAFT);
      await refreshStats();
    } finally {
      setIsBusy(false);
    }
  }, [celebrate, refreshStats]);

  /** Ask the server about one match-pairs link, then update the board. */
  const checkPair = useCallback(
    async (left: string, right: string) => {
      const { attemptId } = useLessonStore.getState();
      if (!attemptId || !exercise) return;
      const { is_correct: isCorrect } = await api.checkMatchPair(
        attemptId,
        exercise.id,
        left,
        right,
      );
      setDraft((current) => ({
        ...current,
        match: isCorrect
          ? {
              pendingLeft: null,
              solved: [...current.match.solved, left],
              wrong: null,
              pairs: [...current.match.pairs, { left, right }],
            }
          : { ...current.match, pendingLeft: null, wrong: [left, right] },
      }));
    },
    [exercise],
  );

  /** Spend gems, then restart the lesson from the top with a full bar. */
  const refill = useCallback(async () => {
    setIsBusy(true);
    try {
      await api.refillHearts(userId);
      await refreshStats();
      await load(lessonId, userId);
      setDraft(EMPTY_DRAFT);
    } finally {
      setIsBusy(false);
    }
  }, [lessonId, userId, load, refreshStats]);

  // Enter checks, then continues — the lesson is fully playable from the
  // keyboard. Skipped while typing, where Enter belongs to the textarea.
  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key !== "Enter" || event.target instanceof HTMLTextAreaElement) return;
      event.preventDefault();
      if (useLessonStore.getState().result) void advance();
      else void check();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [advance, check]);

  return { store, exercise, draft, setDraft, answer, isLastExercise, isBusy, check, advance, checkPair, refill };
}
