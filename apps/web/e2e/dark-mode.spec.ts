import { test, expect } from '@playwright/test'

/**
 * E2E smoke tests for dark mode theme toggle.
 */
test.describe('Dark Mode Toggle', () => {
  test('theme toggle button is visible in site header', async ({ page }) => {
    await page.goto('/pricing')
    // The theme button cycles through light -> dark -> system.
    // Its aria-label is one of: "Light mode", "Dark mode", or "System theme".
    const themeButton = page.getByRole('button', {
      name: /Light mode|Dark mode|System theme/i,
    })
    await expect(themeButton).toBeVisible()
  })

  test('clicking theme toggle adds dark class to html element', async ({
    page,
  }) => {
    await page.goto('/pricing')
    const themeButton = page.getByRole('button', {
      name: /Light mode|Dark mode|System theme/i,
    })

    // Determine initial label and click to reach dark mode.
    const initialLabel = await themeButton.getAttribute('aria-label')

    if (initialLabel === 'Light mode') {
      // light -> dark
      await themeButton.click()
      await expect(page.locator('html')).toHaveClass(/dark/)
    } else if (initialLabel === 'System theme') {
      // system -> light
      await themeButton.click()
      // light -> dark
      await themeButton.click()
      await expect(page.locator('html')).toHaveClass(/dark/)
    } else {
      // Already dark mode — verify class is present
      await expect(page.locator('html')).toHaveClass(/dark/)
    }
  })

  test('clicking theme toggle again removes dark class', async ({ page }) => {
    await page.goto('/pricing')
    const themeButton = page.getByRole('button', {
      name: /Light mode|Dark mode|System theme/i,
    })

    // Click until we reach dark mode, then click once more to system/light.
    const initialLabel = await themeButton.getAttribute('aria-label')

    if (initialLabel === 'Light mode') {
      // light -> dark -> system
      await themeButton.click()
      await themeButton.click()
    } else if (initialLabel === 'Dark mode') {
      // dark -> system
      await themeButton.click()
    } else {
      // system -> light
      await themeButton.click()
    }

    // After exiting dark mode the dark class should be removed
    // (unless system prefers dark, but the test runner defaults to light).
    await expect(page.locator('html')).not.toHaveClass(/\bdark\b/)
  })
})
