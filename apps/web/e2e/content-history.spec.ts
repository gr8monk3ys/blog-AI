import { test, expect } from '@playwright/test'

/**
 * E2E smoke tests for content history route.
 */
test.describe('Content History', () => {
  test('history route responds', async ({ page }) => {
    const response = await page.goto('/history')

    expect(response?.status()).toBeLessThan(500)
    await expect(page).toHaveURL(/.*history.*/)
  })

  test('history page includes history-related content', async ({ page }) => {
    await page.goto('/history')
    await expect(page.locator('body')).toContainText(
      /History|Content|Search|Filter/i
    )
  })
})
