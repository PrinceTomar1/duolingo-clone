/**
 * Join class names, dropping anything falsy.
 *
 * A three-line helper instead of a dependency: conditional classes are the only
 * thing the app needs, and `clsx` as a package would add a build step's worth of
 * nothing. Kept as its own module so every component imports the same one.
 */
export type ClassValue = string | false | null | undefined;

export function clsx(...values: ClassValue[]): string {
  return values.filter(Boolean).join(" ");
}
