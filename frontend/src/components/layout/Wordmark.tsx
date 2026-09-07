/**
 * The "duolingo" wordmark.
 *
 * Set in the app's own Nunito rather than shipped as a logo file: it is the
 * brand's lowercase, extra-bold, tightly-tracked treatment, and keeping it as
 * text means it inherits the theme and scales without an asset.
 */
export function Wordmark({ className }: { className?: string }) {
  return (
    <span className={`select-none font-extrabold lowercase tracking-tight text-feather ${className ?? ""}`}>
      duolingo
    </span>
  );
}
