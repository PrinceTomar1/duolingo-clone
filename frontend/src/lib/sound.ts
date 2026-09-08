/**
 * The two lesson sounds, synthesised in the browser.
 *
 * Generated with the Web Audio API rather than shipped as audio files: two
 * short tones are a few lines of code, and bundling MP3s would add binary
 * assets to a repo that is being read as source.
 *
 * Every call is wrapped defensively -- Safari refuses to create a context
 * before a user gesture, and a blocked sound must never break a lesson.
 */

let context: AudioContext | null = null;

function getContext(): AudioContext | null {
  if (typeof window === "undefined") return null;
  try {
    context ??= new AudioContext();
    // A context created before the first tap starts suspended.
    if (context.state === "suspended") void context.resume();
    return context;
  } catch {
    return null;
  }
}

/** Play one tone. `type` shapes the timbre; the gain envelope avoids clicks. */
function tone(frequency: number, startOffset: number, duration: number, volume: number): void {
  const audio = getContext();
  if (!audio) return;

  const oscillator = audio.createOscillator();
  const gain = audio.createGain();
  const startAt = audio.currentTime + startOffset;

  oscillator.type = "sine";
  oscillator.frequency.setValueAtTime(frequency, startAt);

  // Ramp up over 10ms and decay exponentially, which is what stops the tone
  // from popping at either end.
  gain.gain.setValueAtTime(0.0001, startAt);
  gain.gain.exponentialRampToValueAtTime(volume, startAt + 0.01);
  gain.gain.exponentialRampToValueAtTime(0.0001, startAt + duration);

  oscillator.connect(gain).connect(audio.destination);
  oscillator.start(startAt);
  oscillator.stop(startAt + duration);
}

/** A rising two-note chime for a correct answer. */
export function playCorrect(): void {
  tone(660, 0, 0.12, 0.14);
  tone(880, 0.09, 0.16, 0.12);
}

/** A short falling buzz for a wrong answer. */
export function playIncorrect(): void {
  tone(200, 0, 0.18, 0.16);
  tone(150, 0.1, 0.22, 0.14);
}

/** Whether this browser can attempt speech synthesis at all. */
export function canSpeak(): boolean {
  return typeof window !== "undefined" && "speechSynthesis" in window;
}

/**
 * Resolve once the browser has at least one voice loaded, or after a short
 * timeout -- whichever comes first.
 *
 * Chrome (unlike Safari/Firefox) loads its voice list asynchronously: calling
 * `speak()` before `getVoices()` has ever populated does not error, it just
 * produces silence, which is indistinguishable from the feature being broken.
 * This is the fix for that: wait for the one-time `voiceschanged` event most
 * browsers fire when the list first arrives, capped at 300ms so a browser
 * that never fires it (or never gets a voice at all -- some headless/CI
 * environments) does not hang the speaker button.
 */
function voicesReady(): Promise<void> {
  const synth = window.speechSynthesis;
  if (synth.getVoices().length > 0) return Promise.resolve();
  return new Promise((resolve) => {
    const timer = setTimeout(resolve, 300);
    synth.addEventListener(
      "voiceschanged",
      () => {
        clearTimeout(timer);
        resolve();
      },
      { once: true },
    );
  });
}

interface SpeakCallbacks {
  onStart?: () => void;
  onEnd?: () => void;
  /** Fired for an unsupported browser, or a synthesis engine that errors out. */
  onError?: () => void;
}

/**
 * Speak a phrase aloud in the target language.
 *
 * Uses the browser's own Web Speech API rather than shipped audio files or a
 * third-party TTS service -- no binary assets, no API key, no per-request
 * cost, and it works offline once the voice is cached by the OS. Coverage is
 * real but not universal (a browser with no Spanish voice installed falls
 * back to its default voice rather than failing); `onError` is how a caller
 * turns that into an honest "audio isn't available here" message instead of
 * a speaker button that looks broken.
 *
 * `lang` is a BCP 47 tag ("es-ES"); every exercise in this course speaks
 * Spanish, so callers do not need to plumb the course's language through.
 */
export async function speak(text: string, lang = "es-ES", callbacks: SpeakCallbacks = {}): Promise<void> {
  const { onStart, onEnd, onError } = callbacks;
  if (!canSpeak()) {
    onError?.();
    return;
  }
  try {
    // A new utterance while one is already talking would overlap; cutting the
    // old one off is what a second tap on the speaker icon should do.
    window.speechSynthesis.cancel();
    await voicesReady();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = lang;
    utterance.rate = 0.9;
    utterance.onstart = () => onStart?.();
    utterance.onend = () => onEnd?.();
    utterance.onerror = () => onError?.();
    window.speechSynthesis.speak(utterance);
  } catch {
    onError?.();
  }
}
