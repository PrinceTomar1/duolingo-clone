"use client";

/**
 * Who is logged in, and their live stats.
 *
 * There is no auth in this build, so "the session" is a demo learner resolved
 * by username -- normally the seeded default, but see `switchTo` below. Stats
 * live here rather than in each page because the right rail, the lesson
 * player and the shop all read the same hearts and gems, and every one of
 * them must update the instant a lesson changes them.
 */

import { create } from "zustand";

import { api } from "@/lib/api";
import type { User, UserStats } from "@/types/api";

export const DEMO_USERNAME = "prince";

/** Which learner's data to load. Not real auth: a plain, inspectable choice. */
const ACTIVE_USERNAME_KEY = "duo-active-username";

function readStoredUsername(): string {
  if (typeof window === "undefined") return DEMO_USERNAME;
  try {
    return window.localStorage.getItem(ACTIVE_USERNAME_KEY) ?? DEMO_USERNAME;
  } catch {
    return DEMO_USERNAME;
  }
}

interface SessionState {
  user: User | null;
  stats: UserStats | null;
  isLoading: boolean;
  error: string | null;
  /** Resolve the active learner and their stats. Safe to call repeatedly. */
  bootstrap: () => Promise<void>;
  /**
   * Load a different seeded learner and remember the choice.
   *
   * There is no real login here, so this is the closest honest equivalent to
   * "log out and sign back in as someone else": every seeded learner is an
   * equally valid demo account, and this is how a reviewer can look at more
   * than one without a database console. It does not end a session, because
   * there is no session to end -- it swaps which one is loaded.
   */
  switchTo: (username: string) => Promise<void>;
  /** Re-read stats from the server after something changed them. */
  refreshStats: () => Promise<void>;
  /** Replace stats with a payload the server already returned. */
  applyStats: (stats: UserStats) => void;
}

async function loadUser(username: string, set: (partial: Partial<SessionState>) => void) {
  set({ isLoading: true, error: null });
  try {
    const user = await api.userByUsername(username);
    const stats = await api.stats(user.id);
    set({ user, stats, isLoading: false });
  } catch (error) {
    set({
      isLoading: false,
      error: error instanceof Error ? error.message : "Could not reach the API",
    });
  }
}

export const useSessionStore = create<SessionState>((set, get) => ({
  user: null,
  stats: null,
  isLoading: false,
  error: null,

  bootstrap: async () => {
    // Guard against the double-invoke React 18 StrictMode does in development.
    if (get().user || get().isLoading) return;
    await loadUser(readStoredUsername(), set);
  },

  switchTo: async (username) => {
    try {
      window.localStorage.setItem(ACTIVE_USERNAME_KEY, username);
    } catch {
      // A private-browsing tab that refuses storage still gets the switch for
      // this load; it just will not stick past a refresh.
    }
    await loadUser(username, set);
  },

  refreshStats: async () => {
    const user = get().user;
    if (!user) return;
    set({ stats: await api.stats(user.id) });
  },

  applyStats: (stats) => set({ stats }),
}));
