import { test, expect } from '@playwright/test'

/**
 * E2E smoke tests for key frontend routes.
 */
test.describe('Navigation', () => {
  test('homepage loads successfully', async ({ page }) => {
    const response = await page.goto('/')

    expect(response?.status()).toBeLessThan(500)
    await expect(page).toHaveTitle(/Blog AI/i)
  })

  test('tool directory route loads', async ({ page }) => {
    const response = await page.goto('/tool-directory')

    expect(response?.status()).toBeLessThan(500)
    await expect(page).toHaveURL(/.*tool-directory.*/)
  })

  test('tools route loads', async ({ page }) => {
    const response = await page.goto('/tools')

    expect(response?.status()).toBeLessThan(500)
    await expect(page).toHaveURL(/.*tools.*/)
  })

  test('history route loads', async ({ page }) => {
    const response = await page.goto('/history')

    expect(response?.status()).toBeLessThan(500)
    await expect(page).toHaveURL(/.*history.*/)
  })

  test('pricing route loads', async ({ page }) => {
    const response = await page.goto('/pricing')

    expect(response?.status()).toBeLessThan(500)
    await expect(page).toHaveURL(/.*pricing.*/)
  })

  test('404 page shows for invalid routes', async ({ page }) => {
    const response = await page.goto('/this-page-does-not-exist-12345')

    // Should either show 404 or redirect
    expect(response?.status()).toBeLessThan(500)
  })
})
