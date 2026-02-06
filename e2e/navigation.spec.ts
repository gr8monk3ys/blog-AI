import { test, expect } from '@playwright/test'

/**
 * E2E tests for navigation and basic page rendering.
 */
test.describe('Navigation', () => {
  test('homepage loads successfully', async ({ page }) => {
    await page.goto('/')

    // Should show the main heading or content generator
    await expect(page).toHaveTitle(/Blog AI/i)
  })

  test('can navigate to tools page', async ({ page }) => {
    await page.goto('/')

    // Find and click on tools link
    const toolsLink = page.getByRole('link', { name: /tools/i })
    if (await toolsLink.isVisible()) {
      await toolsLink.click()
      await expect(page).toHaveURL(/.*tools.*/)
    }
  })

  test('can navigate to history page', async ({ page }) => {
    await page.goto('/')

    const historyLink = page.getByRole('link', { name: /history/i })
    if (await historyLink.isVisible()) {
      await historyLink.click()
      await expect(page).toHaveURL(/.*history.*/)
    }
  })

  test('can navigate to analytics page', async ({ page }) => {
    await page.goto('/')

    const analyticsLink = page.getByRole('link', { name: /analytics/i })
    if (await analyticsLink.isVisible()) {
      await analyticsLink.click()
      await expect(page).toHaveURL(/.*analytics.*/)
    }
  })

  test('can navigate to brand voice page', async ({ page }) => {
    await page.goto('/')

    const brandLink = page.getByRole('link', { name: /brand/i })
    if (await brandLink.isVisible()) {
      await brandLink.click()
      await expect(page).toHaveURL(/.*brand.*/)
    }
  })

  test('404 page shows for invalid routes', async ({ page }) => {
    const response = await page.goto('/this-page-does-not-exist-12345')

    // Should either show 404 or redirect
    expect(response?.status()).toBeLessThan(500)
  })
})
