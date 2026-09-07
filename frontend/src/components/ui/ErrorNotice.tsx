import { Icon } from "@/components/ui/Icon";

/**
 * The one place a failed request is rendered.
 *
 * Says what to do about it, because in this build every failure has the same
 * cause: the API is not running.
 */
export function ErrorNotice({ message }: { message: string }) {
  return (
    <div
      role="alert"
      className="mx-auto mt-10 max-w-md rounded-2xl border-2 border-cardinal bg-incorrect-bg p-6 text-center"
    >
      <Icon name="x" size={40} className="mx-auto mb-3 text-cardinal" strokeWidth={3} />
      <h2 className="text-lg font-extrabold text-incorrect-text">Something went wrong</h2>
      <p className="mt-1 text-sm font-bold text-incorrect-text/80">{message}</p>
      <p className="mt-4 text-xs font-bold text-wolf">
        Check that the API is running and that NEXT_PUBLIC_API_URL points at it.
      </p>
    </div>
  );
}
