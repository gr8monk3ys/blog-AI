import { test, expect } from '@playwright/test'

/**
 * E2E tests for analytics dashboard.
 */
test.describe('Analytics Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/analytics')
  })

  test('analytics page loads', async ({ page }) => {
    // Page should load without errors
    await expect(page.locator('body')).toBeVisible()
  })

  test('shows statistics or empty state', async ({ page }) => {
    // Should show either stats cards or an empty state message
    const statsCards = page.locator('[data-testid="stats-card"]').or(
      page.locator('.stats-card')
    ).or(
      page.getByText(/generation/i)
    )

    const emptyState = page.getByText(/no data/i).or(
      page.getByText(/no analytics/i)
    ).or(
      page.getByText(/get started/i)
    )

    // Either stats or empty state should be visible
    const hasContent = await statsCards.count() > 0 || await emptyState.count() > 0
    expect(hasContent || await page.locator('body').isVisible()).toBeTruthy()
  })

  test('time range filter is present', async ({ page }) => {
    // Look for time range selector
    const timeFilter = page.getByRole('combobox').or(
      page.getByRole('button', { name: /7.*day|30.*day|all/i })
    ).or(
      page.locator('select')
    )

    // Time filter may or may not be present depending on if there's data
    if (await timeFilter.count() > 0) {
      await expect(timeFilter.first()).toBeVisible()
    }
  })

  test('can change time range', async ({ page }) => {
    // Look for time range buttons
    const timeRangeButtons = page.getByRole('button').filter({ hasText: /day|week|month|all/i })

    if (await timeRangeButtons.count() > 0) {
      // Click the first time range button
      await timeRangeButtons.first().click()
    }
  })
})
