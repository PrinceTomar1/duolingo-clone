import { THEME_STORAGE_KEY } from "@/store/useThemeStore";

/**
 * Applies the saved theme before React hydrates.
 *
 * Without this, a dark-mode user gets one white frame while the bundle loads.
 * The script is tiny, runs synchronously in `<body>`, and falls back to the OS
 * preference when nothing has been saved yet.
 */
export function ThemeScript() {
  const script = `
    try {
      var saved = localStorage.getItem(${JSON.stringify(THEME_STORAGE_KEY)});
      var prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      if (saved === 'dark' || (!saved && prefersDark)) {
        document.documentElement.classList.add('dark');
      }
    } catch (e) {}
  `;

  return <script dangerouslySetInnerHTML={{ __html: script }} />;
}
