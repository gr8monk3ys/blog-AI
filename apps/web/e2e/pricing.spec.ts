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

  /**
   * The plan cards must be in the server HTML, not fetched after hydration.
   *
   * They used to arrive from GET /api/payments/pricing on the client, which
   * pushed every section below them down the page: mobile CLS 0.359, blamed on
   * the comparison-table section. CI never caught it because CI has no backend
   * on NEXT_PUBLIC_API_URL, so the grid stayed empty and nothing ever shifted.
   * This asserts the document itself, which is true with or without an API.
   */
  test('plan cards are server-rendered in the document', async ({ request }) => {
    const response = await request.get('/pricing')
    expect(response.status()).toBe(200)
    const html = await response.text()

    for (const plan of ['Free', 'Starter', 'Pro']) {
      expect(html).toContain(`>${plan}</h2>`)
    }
    expect(html.match(/included/gi)?.length ?? 0).toBeGreaterThanOrEqual(3)
  })

  test('plan card headings do not skip a level', async ({ page }) => {
    const levels = await page
      .locator('h1, h2, h3, h4, h5, h6')
      .evaluateAll((nodes) => nodes.map((node) => Number(node.tagName.slice(1))))

    expect(levels[0]).toBe(1)
    for (let i = 1; i < levels.length; i += 1) {
      expect(levels[i] - levels[i - 1]).toBeLessThanOrEqual(1)
    }
  })

  test('billing cycle toggle switches between monthly and yearly', async ({
    page,
  }) => {
    const yearlyButton = page.getByRole('button', { name: /yearly/i })
    await yearlyButton.click()
    await expect(page.locator('body')).toContainText(/Save 17%/i)
  })
})
