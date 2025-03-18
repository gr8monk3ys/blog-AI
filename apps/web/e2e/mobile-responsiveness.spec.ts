import { test, expect } from '@playwright/test'

/**
 * E2E smoke tests for mobile responsiveness.
 *
 * Verifies that key pages render correctly at a mobile viewport width
 * and that the mobile navigation menu is accessible.
 */
test.describe('Mobile Responsiveness', () => {
  test.use({ viewport: { width: 375, height: 812 } })

  test('pricing page renders at mobile viewport', async ({ page }) => {
    const response = await page.goto('/pricing')

    expect(response?.status()).toBeLessThan(500)
    await expect(page.locator('body')).toContainText(
      /Pricing For Brand-Safe Content Production/i
    )
  })

  test('tool directory renders at mobile viewport', async ({ page }) => {
    const response = await page.goto('/tool-directory')

    expect(response?.status()).toBeLessThan(500)
    await expect(page.locator('body')).toContainText(
      /Browse every AI tool and calculator/i
    )
  })

  test('sign-in page renders at mobile viewport', async ({ page }) => {
    const response = await page.goto('/sign-in')

    expect(response?.status()).toBeLessThan(500)
    await expect(page.locator('body')).toContainText(
      /sign in|Clerk is not configured/i
    )
  })

  test('mobile hamburger menu button is visible', async ({ page }) => {
    await page.goto('/pricing')
    const menuButton = page.getByRole('button', {
      name: /Open navigation menu/i,
    })
    await expect(menuButton).toBeVisible()
  })

  test('mobile menu opens and shows navigation links', async ({ page }) => {
    await page.goto('/pricing')
    const menuButton = page.getByRole('button', {
      name: /Open navigation menu/i,
    })
    await menuButton.click()

    const mobileNav = page.locator('#mobile-nav')
    await expect(mobileNav).toBeVisible()
    await expect(mobileNav.getByRole('link', { name: /Pricing/i })).toBeVisible()
  })

  test('mobile menu can be closed', async ({ page }) => {
    await page.goto('/pricing')
    const openButton = page.getByRole('button', {
      name: /Open navigation menu/i,
    })
    await openButton.click()
    await expect(page.locator('#mobile-nav')).toBeVisible()

    const closeButton = page.getByRole('button', {
      name: /Close navigation menu/i,
    })
    await closeButton.click()
    await expect(page.locator('#mobile-nav')).not.toBeVisible()
  })
})
