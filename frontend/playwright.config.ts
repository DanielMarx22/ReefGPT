import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
  },
  
  projects: [
    {
      name: 'Frontend (Mocked API)',
      testDir: './tests/e2e',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'AI Intelligence (Real API)',
      testDir: './tests/ai-integration',
      use: { ...devices['Desktop Chrome'] },
    }
  ],
  
  // Assuming the user runs the tests while the dev server is running.
  // If we wanted Playwright to start the servers, we would use webServer config here,
  // but since they are already running in terminals, we will just point to localhost:3000
});
