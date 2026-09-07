import { defineConfig, devices } from "@playwright/test";

/**
 * End-to-end configuration.
 *
 * These specs drive the real UI against a real backend -- no mocking -- because
 * the things worth protecting here (a heart is spent, XP is banked once, a
 * locked skill refuses to open) are decided by the server. A suite that stubbed
 * the API would prove only that the components render.
 *
 * The backend is expected to be running and seeded; see e2e/journey.spec.ts.
 */
export default defineConfig({
  testDir: "./e2e",
  // The specs share one learner, so they must not race each other.
  workers: 1,
  fullyParallel: false,
  timeout: 90_000,
  expect: { timeout: 10_000 },
  reporter: [["list"]],
  use: {
    baseURL: process.env.E2E_BASE_URL ?? "http://localhost:3000",
    trace: "retain-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
