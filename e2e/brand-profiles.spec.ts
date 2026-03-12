import { test, expect } from '@playwright/test'

/**
 * E2E smoke tests for brand profiles route.
 */
test.describe('Brand Profiles', () => {
  test('brand route responds', async ({ page }) => {
    const response = await page.goto('/brand')

    expect(response?.status()).toBeLessThan(500)
    await expect(page).toHaveURL(/.*brand.*/)
  })

  test('brand page includes profile-management content', async ({ page }) => {
    await page.goto('/brand')
    await expect(page.locator('body')).toContainText(
      /Brand|Profile|Voice|Create/i
    )
  })
})
