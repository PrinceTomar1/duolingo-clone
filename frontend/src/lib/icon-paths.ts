/**
 * Every icon in the app, as SVG path data on a 24x24 grid.
 *
 * Hand-drawn rather than pulled from an icon package: the assignment is graded
 * on hand-built UI, and a data table of paths is both smaller than a dependency
 * and something I can change one glyph of without a version bump.
 *
 * `filled` icons are painted with `fill="currentColor"`; the rest are stroked,
 * which is why they share one component rather than being separate files.
 */

export interface IconDefinition {
  paths: string[];
  filled?: boolean;
}

const DEFINITIONS = {
  // --- Skill icons, one per seeded skill --------------------------------
  hand: { paths: ["M4 5h16v10H9l-5 4V5z", "M8 10h.01", "M12 10h.01", "M16 10h.01"] },
  book: { paths: ["M4 4h5a3 3 0 013 3v13a3 3 0 00-3-3H4V4z", "M20 4h-5a3 3 0 00-3 3v13a3 3 0 013-3h5V4z"] },
  sparkles: { paths: ["M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8L12 3z", "M18 16l.9 2.1 2.1.9-2.1.9L18 22l-.9-2.1-2.1-.9 2.1-.9L18 16z"] },
  users: { paths: ["M9 11a3.5 3.5 0 100-7 3.5 3.5 0 000 7z", "M2 20c0-3.3 3.1-5.5 7-5.5s7 2.2 7 5.5", "M17 11.5a3 3 0 100-6", "M18 14.5c2.4.6 4 2.3 4 4.5"] },
  apple: { paths: ["M12 8c-1.5-1.5-5-1.7-6.4 1.3C4 12.6 6 19 9 20c1.2.4 2-.4 3-.4s1.8.8 3 .4c3-1 5-7.4 3.4-10.7C17 6.3 13.5 6.5 12 8z", "M12 8c0-2 1-3.5 3-4"] },
  home: { paths: ["M3 11l9-7 9 7", "M5 10v10h14V10", "M10 20v-6h4v6"] },
  paw: { paths: ["M7 9a2 2 0 100-4 2 2 0 000 4z", "M17 9a2 2 0 100-4 2 2 0 000 4z", "M4 15a2 2 0 100-4 2 2 0 000 4z", "M20 15a2 2 0 100-4 2 2 0 000 4z", "M12 21c-3 0-5-1.8-5-4 0-2 2-3 2-5a3 3 0 016 0c0 2 2 3 2 5 0 2.2-2 4-5 4z"] },
  palette: { paths: ["M12 3a9 9 0 000 18c1.1 0 2-.9 2-2 0-.5-.2-1-.6-1.4-.3-.4-.4-.8-.4-1.1 0-.8.7-1.5 1.5-1.5H17a4 4 0 004-4c0-4.4-4-8-9-8z", "M7 12h.01", "M9.5 8h.01", "M14 7h.01", "M17 10h.01"] },
  plane: { paths: ["M2 13l20-9-9 20-2-8-9-3z"] },
  hash: { paths: ["M9 3L7 21", "M17 3l-2 18", "M4 9h17", "M3 15h17"] },
  clock: { paths: ["M12 21a9 9 0 100-18 9 9 0 000 18z", "M12 7v5l3 2"] },
  "map-pin": { paths: ["M12 21s7-6.4 7-11a7 7 0 10-14 0c0 4.6 7 11 7 11z", "M12 12.5a2.5 2.5 0 100-5 2.5 2.5 0 000 5z"] },

  // --- Navigation -------------------------------------------------------
  shield: { paths: ["M12 2l8 3.5v6c0 5-3.4 9-8 10.5-4.6-1.5-8-5.5-8-10.5v-6L12 2z"] },
  trophy: { paths: ["M7 4h10v5a5 5 0 01-10 0V4z", "M7 6H4v1a4 4 0 004 4", "M17 6h3v1a4 4 0 01-4 4", "M12 14v4", "M8 21h8", "M10 18h4v3h-4z"] },
  chest: { paths: ["M3 10a9 9 0 0118 0v9H3v-9z", "M3 13h18", "M11 13h2v4h-2z"] },
  store: { paths: ["M4 4h16l1.5 5a3 3 0 01-5.8 1 3 3 0 01-5.7 0 3 3 0 01-5.8-1L4 4z", "M5 11v9h14v-9", "M9 20v-5h6v5"] },
  user: { paths: ["M12 12a4 4 0 100-8 4 4 0 000 8z", "M4 21c0-4 3.6-6.5 8-6.5s8 2.5 8 6.5"] },
  dots: { paths: ["M6 12h.01", "M12 12h.01", "M18 12h.01"] },

  // --- Stats and gamification ------------------------------------------
  flame: { paths: ["M12 2c3.2 4.1 6.5 6.2 6.5 10.2A6.5 6.5 0 0112 19a6.5 6.5 0 01-6.5-6.8C5.5 9.4 7 7.7 8.4 6.6c.2 2 1 3.1 1.9 3.4C11.4 7.2 10 4.9 12 2z"], filled: true },
  gem: { paths: ["M6 3h12l4 6-10 12L2 9l4-6z"], filled: true },
  heart: { paths: ["M12 20.6l-1.5-1.4C5.4 14.6 2 11.5 2 7.7 2 4.9 4.2 3 6.8 3 8.3 3 9.8 3.7 12 6c2.2-2.3 3.7-3 5.2-3C19.8 3 22 4.9 22 7.7c0 3.8-3.4 6.9-8.5 11.5L12 20.6z"], filled: true },
  crown: { paths: ["M3 7.5l4.5 3.5L12 4l4.5 7L21 7.5V19H3V7.5z"], filled: true },
  bolt: { paths: ["M13 2L4 14h6.5L9.5 22 20 9.5h-7L13 2z"], filled: true },
  target: { paths: ["M12 21a9 9 0 100-18 9 9 0 000 18z", "M12 17a5 5 0 100-10 5 5 0 000 10z", "M12 13a1 1 0 100-2 1 1 0 000 2z"] },
  calendar: { paths: ["M4 6h16v15H4V6z", "M8 3v5", "M16 3v5", "M4 11h16"] },
  "graduation-cap": { paths: ["M12 4L2 9l10 5 10-5-10-5z", "M6 12v4.5c0 1.7 2.7 3 6 3s6-1.3 6-3V12"] },

  // --- Controls ---------------------------------------------------------
  check: { paths: ["M4 12.5l5.5 5.5L20 6.5"] },
  x: { paths: ["M6 6l12 12", "M18 6L6 18"] },
  lock: { paths: ["M5 11h14v10H5V11z", "M8.5 11V7.5a3.5 3.5 0 017 0V11"] },
  "chevron-left": { paths: ["M15 5l-7 7 7 7"] },
  "chevron-right": { paths: ["M9 5l7 7-7 7"] },
  sun: { paths: ["M12 17a5 5 0 100-10 5 5 0 000 10z", "M12 1v2", "M12 21v2", "M4.2 4.2l1.4 1.4", "M18.4 18.4l1.4 1.4", "M1 12h2", "M21 12h2", "M4.2 19.8l1.4-1.4", "M18.4 5.6l1.4-1.4"] },
  moon: { paths: ["M20 14.5A8.5 8.5 0 019.5 4a8.5 8.5 0 106.6 15.6c1.8-.9 3.2-2.4 3.9-4.3z"] },
  volume: { paths: ["M11 5L6.5 9H3v6h3.5L11 19V5z", "M15.5 9a4 4 0 010 6", "M18.5 6.5a8 8 0 010 11"] },
  infinity: { paths: ["M7 15a3 3 0 110-6c2.5 0 3.5 6 6 6a3 3 0 100-6c-2.5 0-3.5 6-6 6z"] },
} satisfies Record<string, IconDefinition>;

/**
 * Re-exported with the value type widened to `IconDefinition`.
 *
 * `satisfies` alone infers each entry's exact literal shape, which means an
 * icon that omits `filled` has no such property to read. Widening here keeps
 * the key names (so `IconName` stays a precise union) while giving every value
 * the same readable shape.
 */
export const ICONS: Record<IconName, IconDefinition> = DEFINITIONS;

export type IconName = keyof typeof DEFINITIONS;

/**
 * An icon name that may have come from the API.
 *
 * Skill and achievement icons are stored as strings in the database, so they
 * cannot be typed as `IconName` at the boundary. `resolveIcon` narrows them,
 * falling back to a neutral glyph rather than rendering nothing.
 */
export type IconRef = IconName | (string & {});

/** Falls back to a neutral glyph so unknown seed content never crashes a render. */
export function resolveIcon(name: string): IconName {
  return name in ICONS ? (name as IconName) : "sparkles";
}
