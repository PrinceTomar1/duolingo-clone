import { Icon } from "@/components/ui/Icon";

/**
 * The one place a failed request is rendered.
 *
 * Most failures in this build are connectivity, so the setup hint is the
 * default. A refused *domain* action -- a locked skill, a missing lesson -- is
 * not a configuration problem, and telling that learner to check their API URL
 * sends them after the wrong thing, so those callers pass `hint={null}`.
 */
interface ErrorNoticeProps {
  message: string;
  /** `null` hides the hint; omit it to keep the connectivity advice. */
  hint?: string | null;
}

export function ErrorNotice({
  message,
  hint = "Check that the API is running and that NEXT_PUBLIC_API_URL points at it.",
}: ErrorNoticeProps) {
  return (
    <div
      role="alert"
      className="mx-auto mt-10 max-w-md rounded-2xl border-2 border-cardinal bg-incorrect-bg p-6 text-center"
    >
      <Icon name="x" size={40} className="mx-auto mb-3 text-cardinal" strokeWidth={3} />
      <h2 className="text-lg font-extrabold text-incorrect-text">Something went wrong</h2>
      <p className="mt-1 text-sm font-bold text-incorrect-text/80">{message}</p>
      {hint && <p className="mt-4 text-xs font-bold text-wolf">{hint}</p>}
    </div>
  );
}
