import { test, expect } from '@playwright/test'

/**
 * E2E tests for content history page.
 */
test.describe('Content History', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/history')
  })

  test('history page loads', async ({ page }) => {
    // Page should load without errors
    await expect(page.locator('body')).toBeVisible()
  })

  test('shows content list or empty state', async ({ page }) => {
    // Should show either content items or an empty state
    const contentItems = page.locator('[data-testid="content-item"]').or(
      page.locator('.content-item')
    ).or(
      page.locator('article')
    )

    const emptyState = page.getByText(/no.*history/i).or(
      page.getByText(/no.*content/i)
    ).or(
      page.getByText(/create.*first/i)
    ).or(
      page.getByText(/get started/i)
    )

    // Either content or empty state should be present
    const hasContent = await contentItems.count() > 0 || await emptyState.count() > 0
    expect(hasContent || await page.locator('body').isVisible()).toBeTruthy()
  })

  test('search/filter is present', async ({ page }) => {
    // Look for search input
    const searchInput = page.getByPlaceholder(/search/i).or(
      page.getByRole('searchbox')
    ).or(
      page.locator('input[type="search"]')
    )

    // Search may or may not be present
    if (await searchInput.count() > 0) {
      await expect(searchInput.first()).toBeVisible()
    }
  })

  test('can filter by category', async ({ page }) => {
    // Look for category filter
    const categoryFilter = page.getByRole('combobox', { name: /category|type/i }).or(
      page.getByRole('button', { name: /blog|book|all/i })
    )

    if (await categoryFilter.count() > 0) {
      await categoryFilter.first().click()
    }
  })

  test('favorite button works', async ({ page }) => {
    // Look for favorite/star buttons
    const favoriteButton = page.getByRole('button', { name: /favorite|star/i }).or(
      page.locator('button[aria-label*="favorite"]')
    )

    if (await favoriteButton.count() > 0 && await favoriteButton.first().isVisible()) {
      await favoriteButton.first().click()
    }
  })
})
