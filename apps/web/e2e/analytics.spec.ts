import { test, expect } from '@playwright/test'

/**
 * E2E smoke tests for analytics route.
 */
test.describe('Analytics Dashboard', () => {
  test('analytics route responds', async ({ page }) => {
    const response = await page.goto('/analytics')

    expect(response?.status()).toBeLessThan(500)
    await expect(page).toHaveURL(/.*analytics.*/)
  })

  test('sends a signed-out visitor to sign-in and back', async ({ page }) => {
    await page.goto('/analytics')
    await expect(page).toHaveURL(/\/sign-in\?redirect=%2Fanalytics$/)
  })
})
