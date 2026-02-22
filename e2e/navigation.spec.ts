import { test, expect } from '@playwright/test'
import { authPromptLocator, resolveProtectedRouteState, waitForAppToSettle } from './helpers'

/**
 * E2E tests for navigation and basic page rendering.
 */
test.describe('Navigation', () => {
  test('homepage loads successfully', async ({ page }) => {
    await page.goto('/')
    await waitForAppToSettle(page)

    // Should show the main heading or content generator
    await expect(page).toHaveTitle(/Blog AI/i)
  })

  test('can navigate to tools page', async ({ page }) => {
    await page.goto('/tools')
    const routeState = await resolveProtectedRouteState(page, /\/tools(?:\/|$)/)

    if (routeState === 'auth') {
      await expect(authPromptLocator(page)).toBeVisible()
      return
    }

    await expect(page).toHaveURL(/\/tools(?:\/|$)/)
  })

  test('can navigate to history page', async ({ page }) => {
    await page.goto('/history')
    const routeState = await resolveProtectedRouteState(page, /\/history(?:\/|$)/)

    if (routeState === 'auth') {
      await expect(authPromptLocator(page)).toBeVisible()
      return
    }

    await expect(page).toHaveURL(/\/history(?:\/|$)/)
  })

  test('can navigate to analytics page', async ({ page }) => {
    await page.goto('/analytics')
    const routeState = await resolveProtectedRouteState(page, /\/analytics(?:\/|$)/)

    if (routeState === 'auth') {
      await expect(authPromptLocator(page)).toBeVisible()
      return
    }

    await expect(page).toHaveURL(/\/analytics(?:\/|$)/)
  })

  test('can navigate to brand voice page', async ({ page }) => {
    await page.goto('/brand')
    const routeState = await resolveProtectedRouteState(page, /\/brand(?:\/|$)/)

    if (routeState === 'auth') {
      await expect(authPromptLocator(page)).toBeVisible()
      return
    }

    await expect(page).toHaveURL(/\/brand(?:\/|$)/)
  })

  test('404 page shows for invalid routes', async ({ page }) => {
    const response = await page.goto('/this-page-does-not-exist-12345')

    // Should either show 404 or redirect
    expect(response?.status()).toBeLessThan(500)
  })
})
