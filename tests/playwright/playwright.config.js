const { defineConfig, devices } = require("@playwright/test");
const path = require("path");

const repoRoot = path.resolve(__dirname, "..", "..");
const port = process.env.MEMEX_PLAYWRIGHT_PORT || "8091";
const baseURL = process.env.MEMEX_BASE_URL || `http://127.0.0.1:${port}`;

module.exports = defineConfig({
  testDir: path.join(__dirname, "specs"),
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 2 : undefined,
  reporter: [["list"], ["html", { open: "never" }]],
  timeout: 30_000,
  expect: {
    timeout: 10_000,
  },
  outputDir: path.join(__dirname, "test-results"),
  use: {
    baseURL,
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
    viewport: { width: 1440, height: 960 },
  },
  webServer: {
    command: `python -m dashboard.server`,
    url: `${baseURL}/api/status`,
    cwd: repoRoot,
    timeout: 120_000,
    reuseExistingServer: true,
    env: {
      ...process.env,
      PORT: port,
    },
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
