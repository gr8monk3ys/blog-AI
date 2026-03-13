import { test, expect } from '@playwright/test'

/**
 * E2E smoke tests for legal pages (privacy policy and terms of service).
 */
test.describe('Legal Pages', () => {
  test('privacy policy page loads successfully', async ({ page }) => {
    const response = await page.goto('/privacy')

    expect(response?.status()).toBeLessThan(500)
    await expect(page).toHaveURL(/.*privacy.*/)
  })

  test('privacy policy page contains policy content', async ({ page }) => {
    await page.goto('/privacy')
    await expect(page.locator('body')).toContainText(
      /Privacy|Policy|personal information|data/i
    )
  })

  test('terms of service page loads successfully', async ({ page }) => {
    const response = await page.goto('/terms')

    expect(response?.status()).toBeLessThan(500)
    await expect(page).toHaveURL(/.*terms.*/)
  })

  test('terms of service page contains terms content', async ({ page }) => {
    await page.goto('/terms')
    await expect(page.locator('body')).toContainText(
      /Terms|Service|Agreement|conditions/i
    )
  })
})
