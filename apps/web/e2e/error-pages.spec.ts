import { test, expect } from '@playwright/test'

/**
 * E2E smoke tests for error and not-found pages.
 */
test.describe('Error Pages', () => {
  test('404 page renders for a non-existent route', async ({ page }) => {
    const response = await page.goto('/this-route-does-not-exist-xyz-404')

    expect(response?.status()).toBeLessThan(500)
  })

  test('404 page displays "Page not found" heading', async ({ page }) => {
    await page.goto('/this-route-does-not-exist-xyz-404')

    await expect(page.locator('body')).toContainText(/Page not found/i)
  })

  test('404 page displays explanatory text', async ({ page }) => {
    await page.goto('/this-route-does-not-exist-xyz-404')

    await expect(page.locator('body')).toContainText(
      /Sorry, we could not find the page you are looking for/i
    )
  })

  test('404 page has "Go back home" link', async ({ page }) => {
    await page.goto('/this-route-does-not-exist-xyz-404')

    await expect(
      page.getByRole('link', { name: /Go back home/i })
    ).toBeVisible()
  })

  test('404 page has "Go back" button', async ({ page }) => {
    await page.goto('/this-route-does-not-exist-xyz-404')

    await expect(
      page.getByRole('button', { name: /Go back/i })
    ).toBeVisible()
  })

  test('404 page has contact support link', async ({ page }) => {
    await page.goto('/this-route-does-not-exist-xyz-404')

    await expect(
      page.getByRole('link', { name: /contact support/i })
    ).toBeVisible()
  })

  test('"Go back home" link navigates to homepage', async ({ page }) => {
    await page.goto('/this-route-does-not-exist-xyz-404')

    const homeLink = page.getByRole('link', { name: /Go back home/i })
    await expect(homeLink).toHaveAttribute('href', '/')
  })
})
