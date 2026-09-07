/**
 * Small display formatters, kept out of components so they can be reused and
 * reasoned about on their own.
 */

/** "1,240" -- thousands separators for XP and gem counts. */
export function formatNumber(value: number): string {
  return value.toLocaleString("en-US");
}

/** "4:07" -- the completion screen's time card. */
export function formatDuration(totalSeconds: number): string {
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${seconds.toString().padStart(2, "0")}`;
}

/** "27 min" / "1 h 5 min" -- the countdown to the next heart. */
export function formatCountdown(seconds: number): string {
  if (seconds <= 0) return "any moment";
  const minutes = Math.ceil(seconds / 60);
  if (minutes < 60) return `${minutes} min`;
  return `${Math.floor(minutes / 60)} h ${minutes % 60} min`;
}

/** "Mon" -- the profile page's activity chart labels. */
export function weekdayLabel(isoDate: string): string {
  // Parsed as UTC noon so a negative timezone offset cannot roll the label back
  // to the previous day.
  return new Date(`${isoDate}T12:00:00Z`).toLocaleDateString("en-US", { weekday: "short" });
}
