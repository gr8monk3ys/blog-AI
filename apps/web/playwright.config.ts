import { defineConfig, devices } from '@playwright/test'

/**
 * Playwright E2E testing configuration for Blog AI frontend.
 *
 * @see https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  // Directory containing test files
  testDir: './e2e',

  // Run tests within each file in parallel — all specs are stateless smoke tests.
  fullyParallel: true,

  // Fail the build on CI if you accidentally left test.only in the source code
  forbidOnly: !!process.env.CI,

  // Retry on CI only
  retries: process.env.CI ? 2 : 0,

  // 2 parallel workers in CI to balance speed vs dev-server load; auto-detect locally.
  workers: process.env.CI ? 2 : undefined,

  // Reporter to use
  reporter: process.env.CI
    ? [['html', { open: 'never' }], ['github']]
    : [['html', { open: 'on-failure' }]],

  // Shared settings for all projects
  use: {
    // Base URL to use in tests
    baseURL: process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:3000',

    // Collect trace when retrying the failed test
    trace: 'on-first-retry',

    // Screenshot on failure
    screenshot: 'only-on-failure',

    // Video on failure
    video: 'on-first-retry',
  },

  // Configure projects for major browsers
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    // Uncomment for additional browser testing
    // {
    //   name: 'firefox',
    //   use: { ...devices['Desktop Firefox'] },
    // },
    // {
    //   name: 'webkit',
    //   use: { ...devices['Desktop Safari'] },
    // },
  ],

  // Run local dev server before starting the tests
  webServer: {
    // Webpack mode is slower but substantially more stable than Turbopack for e2e startup.
    command:
      'env -u NO_COLOR SUPPRESS_PROXY_AUTH_WARNING=1 PLAYWRIGHT_TEST=1 bun run dev -- -p 3000 --webpack',
    // Use a lightweight route for readiness checks to avoid flakiness on heavier pages.
    url: 'http://localhost:3000/tool-directory',
    reuseExistingServer: false,
    timeout: 180 * 1000,
  },

  // Test timeout
  timeout: 60 * 1000,

  // Expect timeout
  expect: {
    timeout: 5 * 1000,
  },
})
