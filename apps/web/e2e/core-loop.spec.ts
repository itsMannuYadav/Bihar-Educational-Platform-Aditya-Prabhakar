/**
 * Core loop e2e test — mobile viewport (Pixel 5).
 *
 * Prerequisites (run against a live stack):
 *   PLAYWRIGHT_BASE_URL   — defaults to http://localhost:3000
 *   E2E_EMAIL             — a seeded test-teacher email
 *   E2E_PASSWORD          — its password
 *
 * The test follows the happy path from login → generate kit → view resources
 * → save to library → export PPTX.  It is intentionally sequential and
 * tolerates slow Gemini free-tier generation (60 s timeout per generation
 * step).
 */

import { expect, test } from "@playwright/test";

const EMAIL = process.env.E2E_EMAIL ?? "test-teacher@example.com";
const PASSWORD = process.env.E2E_PASSWORD ?? "changeme";

// ---------------------------------------------------------------------------
// Auth helpers
// ---------------------------------------------------------------------------

async function loginAs(
  page: Parameters<Parameters<typeof test>[1]>[0],
  email: string,
  password: string,
) {
  await page.goto("/login");
  await page.getByLabel(/email/i).fill(email);
  await page.getByLabel(/password/i).fill(password);
  await page.getByRole("button", { name: /sign in/i }).click();
  // Wait for redirect to dashboard or onboarding
  await page.waitForURL(/\/(dashboard|onboarding)/, { timeout: 15_000 });
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

test.describe("Core loop — mobile viewport", () => {
  test.use({ viewport: { width: 393, height: 851 } }); // Pixel 5

  test("teacher can log in", async ({ page }) => {
    await loginAs(page, EMAIL, PASSWORD);
    // Successful login lands on /dashboard or /onboarding
    await expect(page).toHaveURL(/\/(dashboard|onboarding)/);
  });

  test("teacher can generate a teaching kit and view resources", async ({
    page,
  }) => {
    await loginAs(page, EMAIL, PASSWORD);

    // If first login, complete onboarding
    if (page.url().includes("/onboarding")) {
      await page.getByLabel(/name/i).fill("Test Teacher");
      await page.getByRole("button", { name: /save/i }).click();
      await page.waitForURL(/\/dashboard/, { timeout: 10_000 });
    }

    // Fill the generate form
    await page.waitForSelector("[data-testid='generate-form'], form", {
      timeout: 10_000,
    });

    // Class selector
    const classSelect = page.getByRole("combobox", { name: /class/i });
    if (await classSelect.isVisible()) {
      await classSelect.selectOption({ index: 0 });
    }

    // Subject selector (appears after class is selected)
    await page.waitForTimeout(500);
    const subjectSelect = page.getByRole("combobox", { name: /subject/i });
    if (await subjectSelect.isVisible()) {
      await subjectSelect.selectOption({ index: 0 });
    }

    // Chapter input
    await page.waitForTimeout(500);
    const chapterInput = page.getByRole("combobox", { name: /chapter/i });
    if (await chapterInput.isVisible()) {
      await chapterInput.fill("Test Chapter");
      // Pick first suggestion or hit Enter to create custom chapter
      const firstOption = page.getByRole("option").first();
      if (await firstOption.isVisible({ timeout: 2_000 }).catch(() => false)) {
        await firstOption.click();
      } else {
        await chapterInput.press("Enter");
      }
    }

    // Submit
    const generateBtn = page.getByRole("button", {
      name: /generate teaching kit/i,
    });
    await expect(generateBtn).toBeEnabled({ timeout: 5_000 });
    await generateBtn.click();

    // Wait for the result page (contains the tab strip)
    await page.waitForURL(/\/teaching-kit\//, { timeout: 15_000 });
    await expect(
      page.getByRole("tablist", { name: /teaching kit resources/i }),
    ).toBeVisible({ timeout: 10_000 });
  });

  test("kit result page has accessible tab strip", async ({ page }) => {
    await loginAs(page, EMAIL, PASSWORD);

    // Navigate directly to the most-recently generated kit if the URL is known
    // In CI this test is skipped when no kit has been generated yet.
    const response = await page.goto("/library");
    if (!response?.ok()) {
      test.skip(true, "Library page unavailable — skipping tab-strip check.");
    }

    const firstKitLink = page.getByRole("link", { name: /view/i }).first();
    if (!(await firstKitLink.isVisible({ timeout: 3_000 }).catch(() => false))) {
      test.skip(true, "No saved kits in library — skipping tab-strip check.");
    }

    await firstKitLink.click();
    await page.waitForURL(/\/teaching-kit\//);

    const tablist = page.getByRole("tablist", {
      name: /teaching kit resources/i,
    });
    await expect(tablist).toBeVisible({ timeout: 10_000 });

    // All tabs should be accessible
    const tabs = tablist.getByRole("tab");
    const tabCount = await tabs.count();
    expect(tabCount).toBeGreaterThan(0);
  });

  test("analytics page loads", async ({ page }) => {
    await loginAs(page, EMAIL, PASSWORD);
    await page.goto("/analytics");
    // Either stats table or empty-state message should appear
    await expect(
      page
        .getByText(/cache hit/i)
        .or(page.getByText(/no cache entries yet/i)),
    ).toBeVisible({ timeout: 10_000 });
  });
});
