"use client";

/**
 * Light/dark preference.
 *
 * The class is written straight onto `<html>` because Tailwind's `dark:`
 * variant is configured in class mode. localStorage keeps the choice across
 * reloads, and `ThemeScript` replays it before first paint so there is no flash.
 */

import { create } from "zustand";

export type Theme = "light" | "dark";

export const THEME_STORAGE_KEY = "duo-theme";

interface ThemeState {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  toggle: () => void;
  /** Adopt whatever the pre-paint script already applied to <html>. */
  hydrate: () => void;
}

function applyTheme(theme: Theme): void {
  document.documentElement.classList.toggle("dark", theme === "dark");
  window.localStorage.setItem(THEME_STORAGE_KEY, theme);
}

export const useThemeStore = create<ThemeState>((set, get) => ({
  theme: "light",

  setTheme: (theme) => {
    applyTheme(theme);
    set({ theme });
  },

  toggle: () => get().setTheme(get().theme === "dark" ? "light" : "dark"),

  hydrate: () => {
    set({ theme: document.documentElement.classList.contains("dark") ? "dark" : "light" });
  },
}));
