/** @type {import('next').NextConfig} */

// The deployed backend, proxied through so the whole app is reachable from one
// URL. `BACKEND_URL` is a plain server-side env var (no NEXT_PUBLIC_ prefix):
// this file and the rewrite it configures both run in Next's own Node server,
// never in the browser, so the backend's real address is never exposed to or
// needed by client code.
const BACKEND_URL = process.env.BACKEND_URL || "https://duolingo-clone-backend-w886.onrender.com";

const nextConfig = {
  reactStrictMode: true,
  // Next infers the workspace root by walking up for the nearest lockfile,
  // and a stray package-lock.json elsewhere in the user's home directory
  // makes it guess wrong. Pinning it to this repo's frontend/ is what it
  // would have found anyway if that other file did not exist.
  outputFileTracingRoot: import.meta.dirname,
  async rewrites() {
    return [
      {
        // Every API call the client makes goes through lib/api.ts as
        // `/api/v1/...`, so one rule covers all of it, including the
        // DEBUG-gated /dev/* routes (they sit under the same prefix).
        source: "/api/v1/:path*",
        destination: `${BACKEND_URL}/api/v1/:path*`,
      },
    ];
  },
};

export default nextConfig;
