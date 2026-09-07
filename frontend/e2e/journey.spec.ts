/**
 * What only a browser can prove.
 *
 * The backend suite already pins the rules (grading, hearts, XP, unlocking).
 * These specs cover the seam above them: that the path is drawn from API state,
 * that the player refuses what the server refuses, and -- the case that used to
 * fail silently -- that a dropped connection tells the learner instead of
 * swallowing the click.
 *
 * Prerequisites: a seeded backend on :8000 and the frontend on :3000, built
 * with NEXT_PUBLIC_API_URL pointing at that backend. See the README.
 */

import { expect, test } from "@playwright/test";

import { DEMO_USER_ID, drainHearts, ensureHearts, firstLessonOf, skills, stats } from "./api";

// Several specs deliberately answer wrongly, so the learner would otherwise run
// out of hearts partway through the run and later specs would fail on ordering.
test.beforeEach(async () => {
  await ensureHearts();
});

test.describe("learning path", () => {
  test("draws unit headers and skill states from the API", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByText(/Unit 1/i).first()).toBeVisible();

    const nodes = await skills(DEMO_USER_ID);
    // The seeded learner is mid-course, so the path must show real variety --
    // a path rendered entirely from one state would pass a weaker assertion.
    const states = new Set(nodes.map((node) => node.state));
    expect(states.has("completed")).toBe(true);
    expect(states.has("locked")).toBe(true);
  });

  test("shows the learner's streak and XP in the chrome", async ({ page }) => {
    const learner = await stats(DEMO_USER_ID);
    await page.goto("/");
    const body = page.locator("body");
    await expect(body).toContainText(String(learner.current_streak));
    await expect(body).toContainText(learner.total_xp.toLocaleString("en-US"));
  });
});

test.describe("lesson player", () => {
  test("keeps Check disabled until an answer exists", async ({ page }) => {
    const open = (await skills(DEMO_USER_ID)).find((node) => node.state !== "locked")!;
    await page.goto(`/lesson/${await firstLessonOf(open.id)}`);

    const check = page.getByRole("button", { name: "Check", exact: true });
    await expect(check).toBeDisabled();
    await page.getByTestId("option").first().click();
    await expect(check).toBeEnabled();
  });

  test("spends a heart for a wrong answer and none for a right one", async ({ page }) => {
    const open = (await skills(DEMO_USER_ID)).find((node) => node.state !== "locked")!;
    const before = await stats(DEMO_USER_ID);
    test.skip(before.hearts < 1, "needs at least one heart to spend");

    await page.goto(`/lesson/${await firstLessonOf(open.id)}`);
    const options = page.getByTestId("option");
    await expect(options.first()).toBeVisible();
    await options.last().click();
    await page.getByRole("button", { name: "Check", exact: true }).click();

    // The spec has no answer key, so it reads the verdict the server sent back
    // and holds the heart rule to *that* -- which is the rule, not a guess.
    const feedback = page.getByRole("status");
    await expect(feedback).toBeVisible();
    const wasCorrect = /Nice!/.test((await feedback.textContent()) ?? "");

    const after = await stats(DEMO_USER_ID);
    expect(after.hearts).toBe(before.hearts - (wasCorrect ? 0 : 1));
    expect(after.hearts).toBeGreaterThanOrEqual(0);
  });

  test("collapses an impatient double-tap into a single submission", async ({ page }) => {
    const open = (await skills(DEMO_USER_ID)).find((node) => node.state !== "locked")!;
    let posts = 0;
    page.on("request", (request) => {
      if (request.method() === "POST" && request.url().includes("/answer")) posts += 1;
    });

    await page.goto(`/lesson/${await firstLessonOf(open.id)}`);
    await page.getByTestId("option").first().click();
    const check = page.getByRole("button", { name: "Check", exact: true });
    await check.click({ clickCount: 2, delay: 30 });
    await expect(page.getByRole("status")).toBeVisible();

    expect(posts).toBe(1);
  });
});

test.describe("refusals are explained", () => {
  test("a locked skill cannot be opened by URL", async ({ page }) => {
    const locked = (await skills(DEMO_USER_ID)).find((node) => node.state === "locked");
    test.skip(!locked, "the seeded learner has finished the whole path");

    await page.goto(`/lesson/${await firstLessonOf(locked!.id)}`);
    const alert = page.getByRole("alert").first();
    await expect(alert).toContainText(/unlock/i);
    // A refusal is not a misconfigured API, so the setup hint stays hidden.
    await expect(alert).not.toContainText(/NEXT_PUBLIC_API_URL/);
    await expect(page.getByRole("button", { name: /back to the path/i })).toBeVisible();
  });

  test("an unknown lesson id reports not found", async ({ page }) => {
    await page.goto("/lesson/999999");
    await expect(page.getByRole("alert").first()).toContainText(/not found/i);
  });
});

test.describe("network failure", () => {
  test("tells the learner, keeps the lesson, and recovers on retry", async ({ page }) => {
    const open = (await skills(DEMO_USER_ID)).find((node) => node.state !== "locked")!;
    await page.goto(`/lesson/${await firstLessonOf(open.id)}`);
    await page.getByTestId("option").first().click();

    let offline = true;
    await page.route("**/api/v1/**", (route) =>
      offline ? route.abort("connectionrefused") : route.continue(),
    );

    const check = page.getByRole("button", { name: "Check", exact: true });
    await check.click();
    await expect(page.getByRole("alert").first()).toContainText(/reach the server/i);
    // The exercise is still on screen: the attempt was not thrown away.
    await expect(check).toBeEnabled();

    offline = false;
    await check.click();
    await expect(page.getByRole("status")).toBeVisible();
    // Next ships its own role="alert" route announcer, so match the banner text
    // rather than counting every alert on the page.
    await expect(page.getByRole("alert").filter({ hasText: /reach the server/i })).toHaveCount(0);
  });
});

test.describe("responsive", () => {
  for (const [label, width] of [["mobile", 390], ["tablet", 768]] as const) {
    test(`${label} renders the lesson without sideways scroll`, async ({ page }) => {
      await page.setViewportSize({ width, height: 844 });
      const open = (await skills(DEMO_USER_ID)).find((node) => node.state !== "locked")!;
      await page.goto(`/lesson/${await firstLessonOf(open.id)}`);
      await expect(page.getByTestId("option").first()).toBeVisible();

      const overflows = await page.evaluate(
        () => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1,
      );
      expect(overflows).toBe(false);
    });
  }
});

test.describe("server-owned numbers reach the UI", () => {
  test("the shop quotes the price the server charges", async ({ page }) => {
    const learner = await stats(DEMO_USER_ID);
    await page.goto("/shop");
    // Hardcoding this in the client once meant the shop could advertise 350
    // while the server charged something else, and gate the button on the
    // wrong figure too.
    await expect(page.locator("body")).toContainText(
      String(learner.heart_refill_gem_cost.toLocaleString("en-US")),
    );
  });

  test("the lesson draws one heart per heart the server allows", async ({ page }) => {
    const learner = await stats(DEMO_USER_ID);
    const open = (await skills(DEMO_USER_ID)).find((node) => node.state !== "locked")!;
    await page.goto(`/lesson/${await firstLessonOf(open.id)}`);
    await expect(page.getByTestId("option").first()).toBeVisible();

    const hearts = await page.locator("header svg, header [aria-hidden]").count();
    expect(hearts).toBeGreaterThanOrEqual(learner.max_hearts);
  });
});

test.describe("an empty heart bar", () => {
  test("offers a way out instead of a dead end", async ({ page }) => {
    const open = (await skills(DEMO_USER_ID)).find((node) => node.state !== "locked")!;
    const lessonId = await firstLessonOf(open.id);
    await drainHearts(DEMO_USER_ID, lessonId);
    const empty = await stats(DEMO_USER_ID);
    expect(empty.hearts).toBe(0);

    // Arriving with no hearts used to land on the generic error notice, whose
    // only control was "Back to the path" -- no heart count, no refill, no
    // countdown. It should be the same screen running dry mid-lesson gives.
    await page.goto(`/lesson/${lessonId}`);
    await expect(page.getByRole("button", { name: /refill/i })).toBeVisible();
    await expect(page.locator("body")).toContainText(
      String(empty.heart_refill_gem_cost.toLocaleString("en-US")),
    );
  });
});

test.describe("error bodies are made readable", () => {
  test("a validation error never reaches the learner as an object", async ({ page }) => {
    await ensureHearts();
    const open = (await skills(DEMO_USER_ID)).find((node) => node.state !== "locked")!;
    await page.goto(`/lesson/${await firstLessonOf(open.id)}`);
    await page.getByTestId("option").first().click();

    // FastAPI sends 422 with `detail` as an array of per-field objects; reading
    // it blindly rendered "[object Object]".
    await page.route("**/api/v1/attempts/**/answer", (route) =>
      route.fulfill({
        status: 422,
        contentType: "application/json",
        body: JSON.stringify({
          detail: [{ type: "int_parsing", loc: ["body", "exercise_id"], msg: "Input should be a valid integer" }],
        }),
      }),
    );
    await page.getByRole("button", { name: "Check", exact: true }).click();

    const banner = page.getByRole("alert").first();
    await expect(banner).toBeVisible();
    await expect(banner).not.toContainText("[object Object]");
    await expect(banner).toContainText(/exercise_id/);
  });
});

test.describe("features that are out of scope", () => {
  test("the guidebook button is inert, not just decorative", async ({ page }) => {
    await page.goto("/");
    const guidebook = page.getByRole("button", { name: /guidebook/i }).first();
    await expect(guidebook).toBeVisible();
    // A live-looking control that swallows taps is worse than an honest one.
    await expect(guidebook).toBeDisabled();
    await expect(guidebook).toHaveAccessibleName(/not part of this build/i);
  });
});
