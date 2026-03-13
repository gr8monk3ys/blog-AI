import { test, expect } from '@playwright/test'

/**
 * E2E smoke tests for the pricing page.
 */
test.describe('Pricing Page', () => {
  test.beforeEach(async ({ page }) => {
    const response = await page.goto('/pricing')
    expect(response?.status()).toBeLessThan(500)
  })

  test('pricing page renders hero heading', async ({ page }) => {
    await expect(page.locator('body')).toContainText(
      /Pricing For Brand-Safe Content Production/i
    )
  })

  test('pricing page shows billing cycle toggle', async ({ page }) => {
    await expect(page.getByRole('button', { name: /monthly/i })).toBeVisible()
    await expect(page.getByRole('button', { name: /yearly/i })).toBeVisible()
  })

  test('pricing page renders feature comparison section', async ({ page }) => {
    await expect(page.locator('body')).toContainText(/Feature Comparison/i)
  })

  test('pricing page renders FAQ section', async ({ page }) => {
    await expect(page.locator('body')).toContainText(
      /Frequently Asked Questions/i
    )
    await expect(page.locator('body')).toContainText(
      /Can I upgrade or downgrade anytime/i
    )
  })

  test('pricing page renders footer CTA', async ({ page }) => {
    await expect(page.locator('body')).toContainText(
      /Ready to create amazing content/i
    )
    await expect(
      page.getByRole('link', { name: /Start Creating for Free/i })
    ).toBeVisible()
  })

  test('billing cycle toggle switches between monthly and yearly', async ({
    page,
  }) => {
    const yearlyButton = page.getByRole('button', { name: /yearly/i })
    await yearlyButton.click()
    await expect(page.locator('body')).toContainText(/Save 17%/i)
  })
})
