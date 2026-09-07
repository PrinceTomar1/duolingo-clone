"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { Icon } from "@/components/ui/Icon";
import { Wordmark } from "@/components/layout/Wordmark";
import { clsx } from "@/lib/clsx";
import { NAV_ITEMS } from "@/lib/navigation";

/**
 * The desktop left rail (>=1024px).
 *
 * Fixed rather than sticky so it never scrolls with the path, which is how the
 * real app behaves. Below `lg` it is hidden entirely and `MobileTabBar` takes
 * over -- the two never render at the same time.
 */
export function Sidebar() {
  const pathname = usePathname();

  return (
    <nav className="fixed inset-y-0 left-0 z-30 hidden w-60 flex-col gap-2 border-r-2 border-swan bg-snow px-3 py-6 dark:border-night-border dark:bg-night lg:flex xl:w-64">
      <Link href="/" className="mb-4 px-3">
        <Wordmark className="text-3xl" />
      </Link>

      {NAV_ITEMS.map((item) => {
        const isActive = pathname === item.href;
        return (
          <Link
            key={item.href}
            href={item.href}
            aria-current={isActive ? "page" : undefined}
            className={clsx(
              "flex items-center gap-4 rounded-xl border-2 px-3 py-2.5 text-sm font-extrabold uppercase tracking-wide transition-colors",
              isActive
                ? "border-macaw bg-macaw/10 text-humpback dark:text-macaw"
                : "border-transparent text-wolf hover:bg-polar dark:text-hare dark:hover:bg-night-raised",
            )}
          >
            <Icon name={item.icon} size={30} className={item.color} />
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
