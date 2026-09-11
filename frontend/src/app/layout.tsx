import type { Metadata, Viewport } from "next";
import { Nunito } from "next/font/google";

import { AppShell } from "@/components/layout/AppShell";
import { ThemeScript } from "@/components/layout/ThemeScript";
import "./globals.css";

/**
 * Nunito is Duolingo's typeface. `next/font` self-hosts it at build time, so
 * there is no render-blocking request to Google and no flash of fallback text.
 * Only the two weights the design actually uses are downloaded.
 */
const nunito = Nunito({
  subsets: ["latin"],
  weight: ["700", "800"],
  variable: "--font-nunito",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Duolingo Clone — Learn a Language",
  description: "A hand-built Duolingo clone: skill path, five exercise types, hearts, streaks and XP.",
};

export const viewport: Viewport = {
  themeColor: "#58CC02",
  width: "device-width",
  initialScale: 1,
  // The lesson player is a full-screen takeover; letting it zoom on a double
  // tap makes tapping word-bank tiles feel broken on mobile.
  maximumScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={nunito.variable} suppressHydrationWarning>
      <body className="font-sans">
        <ThemeScript />
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
