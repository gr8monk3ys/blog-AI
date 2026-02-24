import { test, expect, type Page } from '@playwright/test'
import { resolveProtectedRouteState, waitForAppToSettle } from './helpers'

async function canAccessHistory(page: Page): Promise<boolean> {
  await page.goto('/history')
  const routeState = await resolveProtectedRouteState(page, /\/history(?:\/|$)/)

  if (routeState === 'auth') {
    test.skip(true, 'History route requires authentication in this environment')
    return false
  }

  return true
}

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
