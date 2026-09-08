"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { ExerciseView } from "@/components/exercises/ExerciseView";
import { CompletionScreen } from "@/components/lesson/CompletionScreen";
import { FeedbackBar } from "@/components/lesson/FeedbackBar";
import { LessonHeader } from "@/components/lesson/LessonHeader";
import { OutOfHeartsModal } from "@/components/lesson/OutOfHeartsModal";
import { QuitModal } from "@/components/lesson/QuitModal";
import { useLessonRunner } from "@/components/lesson/useLessonRunner";
import { Button } from "@/components/ui/Button";
import { ErrorNotice } from "@/components/ui/ErrorNotice";
import { Icon } from "@/components/ui/Icon";
import { speakableText } from "@/lib/answers";
import { speak } from "@/lib/sound";
import { useSessionStore } from "@/store/useSessionStore";

/**
 * The full-screen lesson takeover.
 *
 * Layout and the two modals only — the flow lives in `useLessonRunner`, and
 * every rule lives on the server.
 */
export function LessonPlayer({ lessonId, userId }: { lessonId: number; userId: number }) {
  const router = useRouter();
  const stats = useSessionStore((state) => state.stats);
  const [showQuit, setShowQuit] = useState(false);
  const runner = useLessonRunner(lessonId, userId);
  const { store, exercise } = runner;

  if (store.status === "error") {
    return (
      <div className="p-6">
        {/* A locked skill or a missing lesson is a refusal, not a misconfigured
            API, so the setup hint is withheld for those. */}
        <ErrorNotice
          message={store.errorMessage ?? "Something went wrong"}
          hint={store.errorStatus === 0 || store.errorStatus === null ? undefined : null}
        />
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

  // Refused at the door for want of hearts: there is no lesson to draw behind
  // the modal, so it is shown on its own rather than falling through to the
  // loading state below and hanging there.
  if (store.status === "failed" && !store.lesson) {
    return (
      <div className="min-h-screen bg-snow dark:bg-night">
        <OutOfHeartsModal
          gems={stats?.gems ?? 0}
          refillCost={stats?.heart_refill_gem_cost ?? 0}
          secondsUntilNextHeart={stats?.seconds_until_next_heart ?? null}
          isRefilling={runner.isBusy}
          onRefill={() => void runner.refill()}
          onQuit={() => router.push("/")}
        />
      </div>
    );
  }

  if (!store.lesson || !exercise) {
    return (
      <div className="flex min-h-screen items-center justify-center font-extrabold text-wolf">
        Loading…
      </div>
    );
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
        <div className="mb-6 flex items-center justify-center gap-2">
          <h1 className="text-center text-lg font-extrabold sm:text-xl">{exercise.prompt}</h1>
          {(() => {
            const text = speakableText(exercise);
            if (!text) return null;
            return (
              <button
                type="button"
                aria-label="Hear this in Spanish"
                onClick={() => speak(text)}
                className="shrink-0 rounded-full p-1.5 text-macaw transition-colors hover:bg-macaw/10"
              >
                <Icon name="volume" size={22} />
              </button>
            );
          })()}
        </div>
        <ExerciseView
          exercise={exercise}
          draft={runner.draft}
          result={store.result}
          onDraftChange={runner.setDraft}
          onSubmit={() => void runner.check()}
          onPair={(left, right) => void runner.checkPair(left, right)}
        />
      </main>

      {/* A failed request is reported here rather than as a toast: the lesson
          route renders no ToastStack. The exercise stays on screen, so the
          learner can simply press the button again. */}
      {runner.actionError && (
        <div
          role="alert"
          className="mx-auto mb-2 flex w-full max-w-2xl items-center gap-2 px-5 text-sm font-bold text-incorrect-text"
        >
          <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-cardinal text-xs text-white">
            !
          </span>
          <span className="min-w-0 flex-1">{runner.actionError}</span>
        </div>
      )}

      {store.result ? (
        <FeedbackBar
          result={store.result}
          isLastExercise={runner.isLastExercise}
          onContinue={() => void runner.advance()}
        />
      ) : (
        <footer className="border-t-2 border-swan px-4 py-4 dark:border-night-border sm:px-8 sm:py-6">
          <div className="mx-auto flex max-w-2xl justify-end">
            <Button
              variant="primary"
              size="lg"
              disabled={runner.answer === null || runner.isBusy}
              onClick={() => void runner.check()}
              className="w-full sm:w-auto sm:min-w-[10rem]"
            >
              Check
            </Button>
          </div>
        </footer>
      )}

      {showQuit && (
        <QuitModal onCancel={() => setShowQuit(false)} onConfirm={() => router.push("/")} />
      )}

      {store.status === "failed" && (
        <OutOfHeartsModal
          gems={stats?.gems ?? 0}
          refillCost={stats?.heart_refill_gem_cost ?? 0}
          secondsUntilNextHeart={stats?.seconds_until_next_heart ?? null}
          isRefilling={runner.isBusy}
          onRefill={() => void runner.refill()}
          onQuit={() => router.push("/")}
        />
      )}
    </div>
  );
}
