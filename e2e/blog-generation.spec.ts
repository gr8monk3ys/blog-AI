import { test, expect, type Page } from '@playwright/test'
import { resolveProtectedRouteState, waitForAppToSettle } from './helpers'

async function canAccessTools(page: Page): Promise<boolean> {
  await page.goto('/tools')
  const routeState = await resolveProtectedRouteState(page, /\/tools(?:\/|$)/)

  if (routeState === 'auth') {
    test.skip(true, 'Tools route requires authentication in this environment')
    return false
  }

  return true
}

/**
 * E2E smoke tests for generation-related routes.
 */
test.describe('Blog Generation', () => {
  test.beforeEach(async ({ page }) => {
    const response = await page.goto('/tools')
    expect(response?.status()).toBeLessThan(500)
  })

  test('tools route responds and keeps URL stable', async ({ page }) => {
    await expect(page).toHaveURL(/.*tools.*/)
  })

  test('tools page contains generation or tool directory content', async ({ page }) => {
    await expect(page.locator('body')).toContainText(
      /AI Writing Tools|Blog Post Generator|Generate Blog Post|Tool Directory/i
    )
  })

  test('tool detail route responds', async ({ page }) => {
    const response = await page.goto('/tools/blog-post')

    expect(response?.status()).toBeLessThan(500)
    await expect(page).toHaveURL(/.*tools\/blog-post.*/)
  })
})
