import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  globalSetup: './e2e/global-setup.ts',
  globalTeardown: './e2e/global-teardown.ts',
  testDir: './e2e',
  timeout: 30000,
  expect: {
    timeout: 5000,
  },
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    actionTimeout: 5000,
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: [
    {
      command: 'python -m uvicorn vpack.app:app --host 127.0.0.1 --port 8001',
      url: 'http://localhost:8001/api/system/health',
      reuseExistingServer: false,
      cwd: '../',
      timeout: 60000,
    },
    {
      command: 'npm run dev -- --force',
      url: 'http://localhost:3000',
      reuseExistingServer: false,
      cwd: './',
      timeout: 60000,
    },
  ],
});
