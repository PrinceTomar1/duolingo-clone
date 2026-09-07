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
  /** Last failed action, shown in the player until the next attempt succeeds. */
  const [actionError, setActionError] = useState<string | null>(null);

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

  /**
   * Surface a failed request instead of letting the rejection vanish.
   *
   * Every action below talks to the API, and a dropped connection used to
   * reject into nothing: the button re-enabled and the learner was left with no
   * idea why nothing happened.
   *
   * Reported as inline state rather than a toast because `AppShell` renders no
   * `ToastStack` on the lesson route -- the lesson is a full-screen takeover, so
   * a toast raised here would never be seen. The lesson is deliberately left
   * standing (status stays `playing`, the draft survives), so retrying is one
   * more tap rather than a lost attempt.
   */
  const reportFailure = useCallback((cause: unknown) => {
    setActionError(
      cause instanceof Error ? cause.message : "Could not reach the server. Try again.",
    );
  }, []);

  const check = useCallback(async () => {
    if (!answer || isBusy || store.result) return;
    setIsBusy(true);
    setActionError(null);
    try {
      useLessonStore.getState().setDraft(answer);
      await useLessonStore.getState().check();
    } catch (cause) {
      reportFailure(cause);
    } finally {
      setIsBusy(false);
    }
  }, [answer, isBusy, store.result, reportFailure]);

  const advance = useCallback(async () => {
    setIsBusy(true);
    setActionError(null);
    try {
      await useLessonStore.getState().advance();
      const summary = useLessonStore.getState().summary;
      if (summary) celebrate(summary);
      setDraft(EMPTY_DRAFT);
      await refreshStats();
    } catch (cause) {
      reportFailure(cause);
    } finally {
      setIsBusy(false);
    }
  }, [celebrate, refreshStats, reportFailure]);

  /** Ask the server about one match-pairs link, then update the board. */
  const checkPair = useCallback(
    async (left: string, right: string) => {
      const { attemptId } = useLessonStore.getState();
      if (!attemptId || !exercise) return;
      let isCorrect: boolean;
      try {
        ({ is_correct: isCorrect } = await api.checkMatchPair(
          attemptId,
          exercise.id,
          left,
          right,
        ));
      } catch (cause) {
        // Drop the half-made link so the board stays playable.
        setDraft((current) => ({ ...current, match: { ...current.match, pendingLeft: null } }));
        reportFailure(cause);
        return;
      }
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
    [exercise, reportFailure],
  );

  /** Spend gems, then restart the lesson from the top with a full bar. */
  const refill = useCallback(async () => {
    setIsBusy(true);
    setActionError(null);
    try {
      await api.refillHearts(userId);
      await refreshStats();
      await load(lessonId, userId);
      setDraft(EMPTY_DRAFT);
    } catch (cause) {
      // The server refuses a refill the learner cannot afford; its message says
      // which, so show that rather than a generic failure.
      reportFailure(cause);
    } finally {
      setIsBusy(false);
    }
  }, [lessonId, userId, load, refreshStats, reportFailure]);

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

  return {
    store,
    exercise,
    draft,
    setDraft,
    answer,
    isLastExercise,
    isBusy,
    actionError,
    check,
    advance,
    checkPair,
    refill,
  };
}
