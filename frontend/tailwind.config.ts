import type { Config } from "tailwindcss";

/**
 * Duolingo's palette, named the way Duolingo names it.
 *
 * Every colour in the app comes from this file. Nothing anywhere else writes a
 * raw hex value, so a rebrand is one edit here, and a reviewer can check that
 * the UI uses the real brand colours by reading one table.
 */
const config: Config = {
  darkMode: "class",
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        feather: { DEFAULT: "#58CC02", shadow: "#58A700" },
        mask: "#89E219",
        macaw: { DEFAULT: "#1CB0F6", shadow: "#1899D6" },
        cardinal: { DEFAULT: "#FF4B4B", shadow: "#EA2B2B" },
        bee: { DEFAULT: "#FFC800", shadow: "#E5B400" },
        fox: { DEFAULT: "#FF9600", shadow: "#E08600" },
        beetle: { DEFAULT: "#CE82FF", shadow: "#B45CE8" },
        humpback: "#2B70C9",
        eel: "#4B4B4B",
        wolf: "#777777",
        hare: "#AFAFAF",
        swan: "#E5E5E5",
        polar: "#F7F7F7",
        snow: "#FFFFFF",
        // Feedback bar backgrounds, straight from the lesson player.
        correct: { bg: "#D7FFB8", text: "#58A700" },
        incorrect: { bg: "#FFDFE0", text: "#EA2B2B" },
        // Dark-mode surfaces. Duolingo's own dark theme is a deep navy rather
        // than pure black, which keeps the bright accent colours readable.
        night: { DEFAULT: "#131F24", raised: "#202F36", border: "#37464F" },
      },
      fontFamily: {
        // Nunito is loaded by next/font in the root layout; the CSS variable it
        // exposes is wired up here so `font-sans` resolves to it everywhere.
        sans: ["var(--font-nunito)", "ui-rounded", "system-ui", "sans-serif"],
      },
      borderRadius: {
        "2xl": "1rem",
      },
      keyframes: {
        // The wrong-answer shake on an option tile.
        shake: {
          "0%, 100%": { transform: "translateX(0)" },
          "20%, 60%": { transform: "translateX(-6px)" },
          "40%, 80%": { transform: "translateX(6px)" },
        },
        // The idle bounce on the active path node's START bubble.
        "bubble-bounce": {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-6px)" },
        },
        // The feedback bar sliding up from the bottom of the lesson player.
        "slide-up": {
          from: { transform: "translateY(100%)" },
          to: { transform: "translateY(0)" },
        },
        "pop-in": {
          from: { transform: "scale(0.85)", opacity: "0" },
          to: { transform: "scale(1)", opacity: "1" },
        },
      },
      animation: {
        shake: "shake 0.4s ease-in-out",
        "bubble-bounce": "bubble-bounce 1.6s ease-in-out infinite",
        "slide-up": "slide-up 0.25s cubic-bezier(0.22, 1, 0.36, 1)",
        "pop-in": "pop-in 0.3s cubic-bezier(0.22, 1, 0.36, 1)",
      },
    },
  },
  plugins: [],
};

export default config;
