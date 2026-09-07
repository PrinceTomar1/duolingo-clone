"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { Icon } from "@/components/ui/Icon";
import { clsx } from "@/lib/clsx";
import { NAV_ITEMS } from "@/lib/navigation";

/**
 * The bottom tab bar the sidebar collapses into below 1024px.
 *
 * Only the items flagged `showOnMobile` appear, because five 44px targets is
 * the most that fits comfortably at 375px without the labels colliding.
 */
export function MobileTabBar() {
  const pathname = usePathname();
  const items = NAV_ITEMS.filter((item) => item.showOnMobile);

  return (
    <nav className="fixed inset-x-0 bottom-0 z-30 flex border-t-2 border-swan bg-snow pb-[env(safe-area-inset-bottom)] dark:border-night-border dark:bg-night lg:hidden">
      {items.map((item) => {
        const isActive = pathname === item.href;
        return (
          <Link
            key={item.href}
            href={item.href}
            aria-label={item.label}
            aria-current={isActive ? "page" : undefined}
            className={clsx(
              "flex flex-1 flex-col items-center gap-0.5 border-t-4 py-2 transition-colors",
              isActive ? "border-macaw bg-macaw/10" : "border-transparent",
            )}
          >
            <Icon name={item.icon} size={26} className={isActive ? item.color : "text-hare"} />
          </Link>
        );
      })}
    </nav>
  );
}
