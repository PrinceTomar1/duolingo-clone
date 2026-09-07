"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { EMPTY_MATCH_STATE } from "@/components/exercises/MatchPairs";
import { ExerciseView, type ExerciseDraft } from "@/components/exercises/ExerciseView";
import { CompletionScreen } from "@/components/lesson/CompletionScreen";
import { FeedbackBar } from "@/components/lesson/FeedbackBar";
import { LessonHeader } from "@/components/lesson/LessonHeader";
import { OutOfHeartsModal } from "@/components/lesson/OutOfHeartsModal";
import { QuitModal } from "@/components/lesson/QuitModal";
import { Button } from "@/components/ui/Button";
import { ErrorNotice } from "@/components/ui/ErrorNotice";
import { api } from "@/lib/api";
import { buildAnswer } from "@/lib/answers";
import { useLessonStore } from "@/store/useLessonStore";
import { useSessionStore } from "@/store/useSessionStore";

/** How many gems a heart refill costs. Mirrors the backend's setting. */
const REFILL_COST = 350;

const EMPTY_DRAFT: ExerciseDraft = { choice: null, text: "", words: [], match: EMPTY_MATCH_STATE };

/**
 * The full-screen lesson takeover.
 *
 * Owns the flow -- draft, check, feedback, advance -- and delegates every rule
 * to the server: it never decides whether an answer is right, only what to
 * render once the server says.
 */
export function LessonPlayer({ lessonId, userId }: { lessonId: number; userId: number }) {
  const router = useRouter();
  const store = useLessonStore();
  const refreshStats = useSessionStore((state) => state.refreshStats);
  const stats = useSessionStore((state) => state.stats);

  const [draft, setDraft] = useState<ExerciseDraft>(EMPTY_DRAFT);
  const [isBusy, setIsBusy] = useState(false);
  const [showQuit, setShowQuit] = useState(false);

  const { load, reset } = store;
  useEffect(() => {
    void load(lessonId, userId);
    return reset;
  }, [lessonId, userId, load, reset]);

  const exercise = store.lesson?.exercises[store.index];
  const answer = exercise ? buildAnswer(exercise, draft) : null;
  const isLast = store.lesson ? store.index === store.lesson.exercises.length - 1 : false;

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

  async function advance(): Promise<void> {
    setIsBusy(true);
    try {
      await useLessonStore.getState().advance();
      setDraft(EMPTY_DRAFT);
      await refreshStats();
    } finally {
      setIsBusy(false);
    }
  }

  /** Ask the server about one match-pairs link and update the board. */
  async function checkPair(left: string, right: string): Promise<void> {
    const attemptId = store.attemptId;
    if (!attemptId || !exercise) return;
    const { is_correct: isCorrect } = await api.checkMatchPair(attemptId, exercise.id, left, right);
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
  }

  async function refill(): Promise<void> {
    setIsBusy(true);
    try {
      await api.refillHearts(userId);
      await refreshStats();
      // A refilled learner restarts the lesson from the top with a full bar.
      await load(lessonId, userId);
      setDraft(EMPTY_DRAFT);
    } finally {
      setIsBusy(false);
    }
  }

  // Enter checks, then continues -- the whole lesson is playable from the
  // keyboard, which is how the real app behaves on desktop.
  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key !== "Enter" || event.target instanceof HTMLTextAreaElement) return;
      event.preventDefault();
      if (store.result) void advance();
      else void check();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  });

  if (store.status === "error") {
    return (
      <div className="p-6">
        <ErrorNotice message={store.errorMessage ?? "Something went wrong"} />
        <div className="mx-auto mt-4 max-w-md">
          <Button variant="ghost" size="lg" fullWidth onClick={() => router.push("/")}>
            Back to the path
          </Button>
        </div>
      </div>
    );
  }

  if (store.status === "complete" && store.summary) {
    return <CompletionScreen summary={store.summary} onContinue={() => router.push("/")} />;
  }

  if (!store.lesson || !exercise) {
    return <div className="flex min-h-screen items-center justify-center font-extrabold text-wolf">Loading…</div>;
  }

  return (
    <div className="flex min-h-screen flex-col bg-snow dark:bg-night">
      <LessonHeader
        progress={store.index / store.lesson.exercises.length}
        hearts={store.hearts}
        maxHearts={store.maxHearts}
        onQuit={() => setShowQuit(true)}
      />

      <main className="mx-auto flex w-full max-w-2xl flex-1 flex-col justify-center px-5 py-6">
        <h1 className="mb-6 text-center text-lg font-extrabold sm:text-xl">{exercise.prompt}</h1>
        <ExerciseView
          exercise={exercise}
          draft={draft}
          result={store.result}
          onDraftChange={setDraft}
          onSubmit={() => void check()}
          onPair={(left, right) => void checkPair(left, right)}
        />
      </main>

      {store.result ? (
        <FeedbackBar result={store.result} isLastExercise={isLast} onContinue={() => void advance()} />
      ) : (
        <footer className="border-t-2 border-swan px-4 py-4 dark:border-night-border sm:px-8 sm:py-6">
          <div className="mx-auto flex max-w-2xl justify-end">
            <Button
              variant="primary"
              size="lg"
              disabled={answer === null || isBusy}
              onClick={() => void check()}
              className="w-full sm:w-auto sm:min-w-[10rem]"
            >
              Check
            </Button>
          </div>
        </footer>
      )}

      {showQuit && <QuitModal onCancel={() => setShowQuit(false)} onConfirm={() => router.push("/")} />}

      {store.status === "failed" && (
        <OutOfHeartsModal
          gems={stats?.gems ?? 0}
          refillCost={REFILL_COST}
          secondsUntilNextHeart={stats?.seconds_until_next_heart ?? null}
          isRefilling={isBusy}
          onRefill={() => void refill()}
          onQuit={() => router.push("/")}
        />
      )}
    </div>
  );
}
