import { test, expect, type Page } from '@playwright/test'
import { resolveProtectedRouteState, waitForAppToSettle } from './helpers'

async function canAccessAnalytics(page: Page) {
  await page.goto('/analytics')
  const routeState = await resolveProtectedRouteState(page, /\/analytics(?:\/|$)/)

  if (routeState === 'auth') {
    test.skip(true, 'Analytics route requires authentication in this environment')
    return false
  }

  return true
}

/**
 * E2E smoke tests for analytics route.
 */
test.describe('Analytics Dashboard', () => {
  test('analytics route responds', async ({ page }) => {
    const response = await page.goto('/analytics')

    expect(response?.status()).toBeLessThan(500)
    await expect(page).toHaveURL(/.*analytics.*/)
  })

  test('analytics page includes dashboard content', async ({ page }) => {
    await page.goto('/analytics')
    await expect(page.locator('body')).toContainText(
      /Analytics Dashboard|Track your content generation|Quick Actions/i
    )
  })
})
