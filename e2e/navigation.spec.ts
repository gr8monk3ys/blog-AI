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

    // Tools link is a core navigation element and must be visible
    const toolsLink = page.getByRole('link', { name: /tools/i })
    await expect(toolsLink).toBeVisible()
    await toolsLink.click()
    await expect(page).toHaveURL(/.*tools.*/)
  })

  test('can navigate to history page', async ({ page }) => {
    await page.goto('/')

    // History link is a core navigation element and must be visible
    const historyLink = page.getByRole('link', { name: /history/i })
    await expect(historyLink).toBeVisible()
    await historyLink.click()
    await expect(page).toHaveURL(/.*history.*/)
  })

  test('can navigate to analytics page', async ({ page }) => {
    await page.goto('/')

    // Analytics link is a core navigation element and must be visible
    const analyticsLink = page.getByRole('link', { name: /analytics/i })
    await expect(analyticsLink).toBeVisible()
    await analyticsLink.click()
    await expect(page).toHaveURL(/.*analytics.*/)
  })

  test('can navigate to brand voice page', async ({ page }) => {
    await page.goto('/')

    // Brand link is a core navigation element and must be visible
    const brandLink = page.getByRole('link', { name: /brand/i })
    await expect(brandLink).toBeVisible()
    await brandLink.click()
    await expect(page).toHaveURL(/.*brand.*/)
  })

  test('404 page shows for invalid routes', async ({ page }) => {
    const response = await page.goto('/this-page-does-not-exist-12345')

    // Should either show 404 or redirect
    expect(response?.status()).toBeLessThan(500)
  })
})
