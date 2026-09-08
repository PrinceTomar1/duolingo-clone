"use client";

import { usePathname } from "next/navigation";
import { useEffect, useLayoutEffect } from "react";

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

  // Theme hydration is a `useLayoutEffect`, not a plain `useEffect`: the store
  // starts at a hardcoded "light" (there is no DOM to read from during server
  // rendering), while `<html>` may already carry `dark` from ThemeScript's
  // pre-paint tag. A passive effect fires *after* the browser paints, which
  // left a real window where the Settings toggle visually showed "off" while
  // the page was already dark -- and a tap in that window read the stale
  // "light" state and asked to turn dark *on*, which was a no-op the learner
  // felt as the button not working. A layout effect runs synchronously before
  // that first paint, so the toggle is correct before it is ever visible or
  // clickable. `bootstrap` stays a plain effect: it is a network call with no
  // equivalent visual race.
  useLayoutEffect(() => {
    hydrateTheme();
  }, [hydrateTheme]);

  useEffect(() => {
    void bootstrap();
  }, [bootstrap]);

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
