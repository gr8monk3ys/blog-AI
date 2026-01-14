---
name: webapp-testing
description: Use this skill for browser automation, E2E testing, visual regression testing, and web application testing with Playwright or similar tools.
---

# Web Application Testing Skill

You have expertise in end-to-end testing, browser automation, and web application quality assurance.

## When to Use

This skill activates for:
- Writing Playwright/Puppeteer tests
- E2E testing strategies
- Visual regression testing
- Cross-browser testing
- Accessibility testing automation
- Performance testing with browsers

## Playwright Test Patterns

### Basic Test Structure
```typescript
// tests/example.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Feature: User Authentication', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
  });

  test('should login with valid credentials', async ({ page }) => {
    await page.fill('[data-testid="email"]', 'user@example.com');
    await page.fill('[data-testid="password"]', 'password123');
    await page.click('[data-testid="submit"]');

    await expect(page).toHaveURL('/dashboard');
    await expect(page.locator('[data-testid="welcome"]')).toContainText('Welcome');
  });

  test('should show error for invalid credentials', async ({ page }) => {
    await page.fill('[data-testid="email"]', 'wrong@example.com');
    await page.fill('[data-testid="password"]', 'wrongpassword');
    await page.click('[data-testid="submit"]');

    await expect(page.locator('[data-testid="error"]')).toBeVisible();
  });
});
```

### Page Object Model
```typescript
// pages/LoginPage.ts
import { Page, Locator } from '@playwright/test';

export class LoginPage {
  readonly page: Page;
  readonly emailInput: Locator;
  readonly passwordInput: Locator;
  readonly submitButton: Locator;
  readonly errorMessage: Locator;

  constructor(page: Page) {
    this.page = page;
    this.emailInput = page.locator('[data-testid="email"]');
    this.passwordInput = page.locator('[data-testid="password"]');
    this.submitButton = page.locator('[data-testid="submit"]');
    this.errorMessage = page.locator('[data-testid="error"]');
  }

  async goto() {
    await this.page.goto('/login');
  }

  async login(email: string, password: string) {
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.submitButton.click();
  }
}

// Usage in test
test('login test', async ({ page }) => {
  const loginPage = new LoginPage(page);
  await loginPage.goto();
  await loginPage.login('user@example.com', 'password');
});
```

### API Mocking
```typescript
test('should handle API errors gracefully', async ({ page }) => {
  // Mock API to return error
  await page.route('**/api/users', route => {
    route.fulfill({
      status: 500,
      body: JSON.stringify({ error: 'Server error' }),
    });
  });

  await page.goto('/users');
  await expect(page.locator('[data-testid="error-state"]')).toBeVisible();
});

// Mock successful response
await page.route('**/api/data', route => {
  route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ items: [{ id: 1, name: 'Test' }] }),
  });
});
```

### Visual Regression Testing
```typescript
test('visual regression: homepage', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveScreenshot('homepage.png', {
    fullPage: true,
    animations: 'disabled',
  });
});

test('visual regression: component states', async ({ page }) => {
  await page.goto('/components');

  // Default state
  await expect(page.locator('.button')).toHaveScreenshot('button-default.png');

  // Hover state
  await page.locator('.button').hover();
  await expect(page.locator('.button')).toHaveScreenshot('button-hover.png');
});
```

### Accessibility Testing
```typescript
import AxeBuilder from '@axe-core/playwright';

test('should pass accessibility audit', async ({ page }) => {
  await page.goto('/');

  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa'])
    .analyze();

  expect(results.violations).toEqual([]);
});
```

## Configuration

### playwright.config.ts
```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['html'],
    ['json', { outputFile: 'test-results.json' }],
  ],
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
    { name: 'mobile', use: { ...devices['iPhone 13'] } },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
});
```

## Test Utilities

### Waiting Strategies
```typescript
// Wait for network idle
await page.waitForLoadState('networkidle');

// Wait for specific response
const response = await page.waitForResponse('**/api/data');

// Wait for element state
await page.locator('.spinner').waitFor({ state: 'hidden' });

// Custom wait
await page.waitForFunction(() => {
  return document.querySelectorAll('.item').length > 0;
});
```

### Authentication State
```typescript
// Save auth state
await page.context().storageState({ path: 'auth.json' });

// Reuse auth state
test.use({ storageState: 'auth.json' });
```

## Best Practices

1. **Use data-testid** - Stable selectors that survive refactoring
2. **Test user flows** - Not implementation details
3. **Isolate tests** - Each test should be independent
4. **Mock external services** - Don't depend on third parties
5. **Run in CI** - Automated testing on every PR
