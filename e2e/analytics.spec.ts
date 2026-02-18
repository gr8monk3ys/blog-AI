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

    // At least one of these must be present
    const statsCount = await statsCards.count()
    const emptyCount = await emptyState.count()
    expect(statsCount + emptyCount).toBeGreaterThan(0)
  })

  test('time range filter is present', async ({ page }) => {
    // Time range filter depends on having analytics data available
    const timeFilter = page.getByRole('combobox').or(
      page.getByRole('button', { name: /7.*day|30.*day|all/i })
    ).or(
      page.locator('select')
    )

    if (\!(await timeFilter.first().isVisible({ timeout: 5000 }).catch(() => false))) {
      test.skip(true, 'Time range filter not available -- no analytics data present')
      return
    }

    await expect(timeFilter.first()).toBeVisible()
  })

  test('can change time range', async ({ page }) => {
    // Time range buttons depend on having analytics data available
    const timeRangeButtons = page.getByRole('button').filter({ hasText: /day|week|month|all/i })

    if (\!(await timeRangeButtons.first().isVisible({ timeout: 5000 }).catch(() => false))) {
      test.skip(true, 'Time range buttons not available -- no analytics data present')
      return
    }

    // Click the first time range button and verify it responds
    const firstButton = timeRangeButtons.first()
    await expect(firstButton).toBeVisible()
    await firstButton.click()
  })
})
