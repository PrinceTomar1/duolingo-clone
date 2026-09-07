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
