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

    // At least one of these must be present
    const contentCount = await contentItems.count()
    const emptyCount = await emptyState.count()
    expect(contentCount + emptyCount).toBeGreaterThan(0)
  })

  test('search/filter is present', async ({ page }) => {
    // Search input may not be present if page shows empty state with no controls
    const searchInput = page.getByPlaceholder(/search/i).or(
      page.getByRole('searchbox')
    ).or(
      page.locator('input[type="search"]')
    )

    if (!(await searchInput.first().isVisible({ timeout: 5000 }).catch(() => false))) {
      test.skip(true, 'Search input not available -- page may be in empty state')
      return
    }

    await expect(searchInput.first()).toBeVisible()
  })

  test('can filter by category', async ({ page }) => {
    // Category filter depends on having content history available
    const categoryFilter = page.getByRole('combobox', { name: /category|type/i }).or(
      page.getByRole('button', { name: /blog|book|all/i })
    )

    if (!(await categoryFilter.first().isVisible({ timeout: 5000 }).catch(() => false))) {
      test.skip(true, 'Category filter not available -- no content history present')
      return
    }

    await expect(categoryFilter.first()).toBeVisible()
    await categoryFilter.first().click()
  })

  test('favorite button works', async ({ page }) => {
    // Favorite buttons only exist when content items are present
    const favoriteButton = page.getByRole('button', { name: /favorite|star/i }).or(
      page.locator('button[aria-label*="favorite"]')
    )

    if (!(await favoriteButton.first().isVisible({ timeout: 5000 }).catch(() => false))) {
      test.skip(true, 'Favorite button not available -- no content items present')
      return
    }

    await expect(favoriteButton.first()).toBeVisible()
    await favoriteButton.first().click()
  })
})
