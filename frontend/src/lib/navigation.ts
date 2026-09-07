import type { IconName } from "@/lib/icon-paths";

/**
 * The single description of the app's navigation.
 *
 * The desktop sidebar and the mobile tab bar are two renderings of this one
 * array, so a new destination can never appear in one and be missing from the
 * other.
 */
export interface NavItem {
  href: string;
  label: string;
  icon: IconName;
  /** Duolingo tints each nav icon its own colour, even when inactive. */
  color: string;
  /** Quests and More are not part of the graded scope; see README. */
  showOnMobile: boolean;
}

export const NAV_ITEMS: NavItem[] = [
  { href: "/", label: "Learn", icon: "shield", color: "text-feather", showOnMobile: true },
  { href: "/leaderboard", label: "Leaderboards", icon: "trophy", color: "text-bee", showOnMobile: true },
  { href: "/quests", label: "Quests", icon: "chest", color: "text-fox", showOnMobile: false },
  { href: "/shop", label: "Shop", icon: "store", color: "text-cardinal", showOnMobile: true },
  { href: "/profile", label: "Profile", icon: "user", color: "text-macaw", showOnMobile: true },
  { href: "/settings", label: "More", icon: "dots", color: "text-wolf", showOnMobile: true },
];
