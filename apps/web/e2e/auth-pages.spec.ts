import { test, expect } from '@playwright/test'

/**
 * E2E smoke tests for sign-in and sign-up pages.
 */
test.describe('Auth Pages', () => {
  test('sign-in page loads successfully', async ({ page }) => {
    const response = await page.goto('/sign-in')

    expect(response?.status()).toBeLessThan(500)
    await expect(page).toHaveURL(/.*sign-in.*/)
  })

  test('sign-in page renders auth UI or configuration notice', async ({
    page,
  }) => {
    await page.goto('/sign-in')
    // When Clerk is configured, the sign-in widget renders.
    // When Clerk is not configured, a fallback message is shown.
    await expect(page.locator('body')).toContainText(
      /sign in|Clerk is not configured/i
    )
  })

  test('sign-up page loads successfully', async ({ page }) => {
    const response = await page.goto('/sign-up')

    expect(response?.status()).toBeLessThan(500)
    await expect(page).toHaveURL(/.*sign-up.*/)
  })

  test('sign-up page renders auth UI or configuration notice', async ({
    page,
  }) => {
    await page.goto('/sign-up')
    await expect(page.locator('body')).toContainText(
      /sign up|Clerk is not configured/i
    )
  })

  test('sign-in page includes site header', async ({ page }) => {
    await page.goto('/sign-in')
    await expect(page.getByRole('banner')).toBeVisible()
  })

  test('sign-up page includes site footer', async ({ page }) => {
    await page.goto('/sign-up')
    await expect(page.getByRole('contentinfo')).toBeVisible()
  })
})
