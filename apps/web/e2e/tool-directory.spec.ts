import { test, expect } from '@playwright/test'

/**
 * E2E smoke tests for the tool directory page.
 */
test.describe('Tool Directory', () => {
  test.beforeEach(async ({ page }) => {
    const response = await page.goto('/tool-directory')
    expect(response?.status()).toBeLessThan(500)
  })

  test('tool directory renders page heading', async ({ page }) => {
    await expect(page.locator('body')).toContainText(
      /Browse every AI tool and calculator in one place/i
    )
  })

  test('tool directory renders category jump links', async ({ page }) => {
    await expect(page.locator('body')).toContainText(/Jump to category/i)
  })

  test('tool directory shows stats section', async ({ page }) => {
    await expect(page.locator('body')).toContainText(
      /Tools in the directory/i
    )
    await expect(page.locator('body')).toContainText(
      /Categories covered/i
    )
  })

  test('tool directory has link to interactive tools page', async ({
    page,
  }) => {
    await expect(
      page.getByRole('link', { name: /Open Interactive Tools/i })
    ).toBeVisible()
  })

  test('tool directory renders internal-linking CTA section', async ({
    page,
  }) => {
    await expect(page.locator('body')).toContainText(
      /Build internal links and topical authority/i
    )
    await expect(
      page.getByRole('link', { name: /Explore templates/i })
    ).toBeVisible()
  })

  test('tool directory includes site header and footer', async ({ page }) => {
    await expect(page.getByRole('banner')).toBeVisible()
    await expect(page.getByRole('contentinfo')).toBeVisible()
  })
})
