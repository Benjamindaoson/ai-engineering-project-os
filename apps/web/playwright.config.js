// @ts-check
const { defineConfig, devices } = require('@playwright/test');

/** @type {import('@playwright/test').PlaywrightTestConfig} */
const config = defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: false,
  retries: 0,
  use: {
    baseURL: 'http://localhost:3001',
    trace: 'on-first-retry',
    headless: true,
  },
  // Start servers automatically before running tests
  webServer: {
    command: 'npm run dev:3001',
    port: 3001,
    reuseExistingServer: true,
    timeout: 120000,
    stdout: 'pipe',
    stderr: 'pipe',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});

module.exports = config;
