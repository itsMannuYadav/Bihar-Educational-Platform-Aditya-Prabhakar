import { defineConfig, devices } from "@playwright/test";

const BASE_URL = process.env.PLAYWRIGHT_BASE_URL ?? "http://localhost:3000";

export default defineConfig({
  testDir: "./e2e",
  timeout: 60_000,
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? "github" : "list",
  use: {
    baseURL: BASE_URL,
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "mobile-chrome",
      use: { ...devices["Pixel 5"] },
    },
    {
      name: "desktop-chrome",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  // Start the Next.js dev server automatically during local runs
  webServer: process.env.CI
    ? undefined
    : {
        command: "npm run dev --workspace=apps/web",
        url: BASE_URL,
        reuseExistingServer: true,
        timeout: 120_000,
      },
});
