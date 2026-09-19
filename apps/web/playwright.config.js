// @ts-check
const { defineConfig, devices } = require('@playwright/test');

/** @type {import('@playwright/test').PlaywrightTestConfig} */
const config = defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: false,
  retries: 0,
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    headless: true,
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});

module.exports = config;
