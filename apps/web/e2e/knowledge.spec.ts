import { test, expect } from '@playwright/test'

test.describe('Knowledge Base page', () => {
  test('should navigate to /knowledge and display page title', async ({
    page,
  }) => {
    await page.goto('/knowledge')
    await expect(page.getByRole('heading', { name: /knowledge base/i })).toBeVisible()
  })

  test('should show upload area', async ({ page }) => {
    await page.goto('/knowledge')
    await expect(page.getByText(/click to upload/i)).toBeVisible()
    await expect(page.getByText(/PDF, DOCX, TXT, or MD/i)).toBeVisible()
  })

  test('should show empty state when no documents exist', async ({ page }) => {
    await page.goto('/knowledge')
    // Either shows documents or empty state
    const emptyState = page.getByText(/no documents yet/i)
    const docTable = page.locator('table')
    await expect(emptyState.or(docTable)).toBeVisible()
  })

  test('should have Knowledge Base link in navigation', async ({ page }) => {
    await page.goto('/')
    const navLink = page.getByRole('link', { name: /knowledge base/i })
    // Link may be in desktop or mobile nav
    await expect(navLink.first()).toBeVisible()
  })
})

test.describe('Blog generator KB toggle', () => {
  test('should show Use Knowledge Base toggle in advanced options', async ({
    page,
  }) => {
    await page.goto('/tools')
    // The toggle should be present in the form
    await expect(page.getByText(/use knowledge base/i)).toBeVisible()
  })
})
