"use client";

/**
 * Who is logged in, and their live stats.
 *
 * There is no auth in this build, so "the session" is the demo learner resolved
 * by username on first load. Stats live here rather than in each page because
 * the right rail, the lesson player and the shop all read the same hearts and
 * gems, and every one of them must update the instant a lesson changes them.
 */

import { create } from "zustand";

import { api } from "@/lib/api";
import type { User, UserStats } from "@/types/api";

export const DEMO_USERNAME = "prince";

interface SessionState {
  user: User | null;
  stats: UserStats | null;
  isLoading: boolean;
  error: string | null;
  /** Resolve the demo learner and their stats. Safe to call repeatedly. */
  bootstrap: () => Promise<void>;
  /** Re-read stats from the server after something changed them. */
  refreshStats: () => Promise<void>;
  /** Replace stats with a payload the server already returned. */
  applyStats: (stats: UserStats) => void;
}

export const useSessionStore = create<SessionState>((set, get) => ({
  user: null,
  stats: null,
  isLoading: false,
  error: null,

  bootstrap: async () => {
    // Guard against the double-invoke React 18 StrictMode does in development.
    if (get().user || get().isLoading) return;
    set({ isLoading: true, error: null });
    try {
      const user = await api.userByUsername(DEMO_USERNAME);
      const stats = await api.stats(user.id);
      set({ user, stats, isLoading: false });
    } catch (error) {
      set({
        isLoading: false,
        error: error instanceof Error ? error.message : "Could not reach the API",
      });
    }
  },

  refreshStats: async () => {
    const user = get().user;
    if (!user) return;
    set({ stats: await api.stats(user.id) });
  },

  applyStats: (stats) => set({ stats }),
}));
