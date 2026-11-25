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

  test('sign-in page renders the sign-in form', async ({ page }) => {
    await page.goto('/sign-in')
    await expect(page.getByLabel('Email')).toBeVisible()
    await expect(page.getByLabel('Password')).toBeVisible()
    await expect(page.getByRole('button', { name: 'Sign In' })).toBeVisible()
  })

  test('sign-up page loads successfully', async ({ page }) => {
    const response = await page.goto('/sign-up')

    expect(response?.status()).toBeLessThan(500)
    await expect(page).toHaveURL(/.*sign-up.*/)
  })

  test('sign-up page renders the sign-up form', async ({ page }) => {
    await page.goto('/sign-up')
    await expect(page.getByLabel('Name')).toBeVisible()
    await expect(page.getByRole('button', { name: 'Create Account' })).toBeVisible()
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
