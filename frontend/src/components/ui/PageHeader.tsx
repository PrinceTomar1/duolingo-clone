/** The title block every non-Learn page opens with. */
export function PageHeader({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <header className="mb-6 border-b-2 border-swan pb-4 dark:border-night-border">
      <h1 className="text-2xl font-extrabold">{title}</h1>
      {subtitle && <p className="mt-1 text-sm font-bold text-wolf">{subtitle}</p>}
    </header>
  );
}
