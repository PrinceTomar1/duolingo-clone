"use client";

import { usePathname } from "next/navigation";
import { useEffect } from "react";

import { MobileTabBar } from "@/components/layout/MobileTabBar";
import { MobileTopBar } from "@/components/layout/MobileTopBar";
import { RightRail } from "@/components/layout/RightRail";
import { Sidebar } from "@/components/layout/Sidebar";
import { ToastStack } from "@/components/ui/ToastStack";
import { useSessionStore } from "@/store/useSessionStore";
import { useThemeStore } from "@/store/useThemeStore";

/**
 * The persistent chrome around every page.
 *
 * The lesson player is deliberately excluded: Duolingo takes over the whole
 * screen during a lesson so nothing competes with the exercise, and rendering
 * the chrome behind a full-screen overlay would leave it reachable by keyboard.
 */
export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const bootstrap = useSessionStore((state) => state.bootstrap);
  const hydrateTheme = useThemeStore((state) => state.hydrate);

  useEffect(() => {
    void bootstrap();
    hydrateTheme();
  }, [bootstrap, hydrateTheme]);

  if (pathname.startsWith("/lesson/")) {
    return <>{children}</>;
  }

  return (
    <div className="min-h-screen">
      <Sidebar />
      <RightRail />
      {/* Margins match the two fixed rails exactly, so content is centred in
          the space that is actually left rather than under a rail. */}
      <div className="lg:ml-60 xl:ml-64 xl:mr-[22rem]">
        <MobileTopBar />
        <main className="mx-auto w-full max-w-2xl px-4 pb-24 pt-4 lg:pb-10">{children}</main>
      </div>
      <MobileTabBar />
      {/* Raised by the lesson player, shown on whatever screen the learner
          lands on afterwards. */}
      <ToastStack />
    </div>
  );
}
