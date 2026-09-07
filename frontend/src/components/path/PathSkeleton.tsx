/**
 * Loading placeholder for the path.
 *
 * Mirrors the real trail's winding offsets so the layout does not jump when the
 * data lands -- a skeleton that sits in the wrong place is worse than none.
 */
export function PathSkeleton() {
  return (
    <div className="animate-pulse" aria-label="Loading your path" role="status">
      <div className="mb-8 h-16 rounded-2xl bg-swan dark:bg-night-raised" />
      <div className="flex flex-col items-center gap-6">
        {Array.from({ length: 5 }, (_, index) => (
          <div
            key={index}
            style={{ transform: `translateX(calc(${Math.sin(index * 0.8).toFixed(3)} * min(26vw, 120px)))` }}
            className="h-[72px] w-[72px] rounded-full bg-swan dark:bg-night-raised"
          />
        ))}
      </div>
    </div>
  );
}
