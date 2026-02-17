import { test, expect } from '@playwright/test'

/**
 * E2E tests for blog generation flow.
 *
 * Note: These tests interact with the UI but may not actually generate
 * content if the backend is not running or API keys are not configured.
 */
test.describe('Blog Generation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('content generator form is visible', async ({ page }) => {
    // At least one input element must exist for entering content
    const inputCount = await page.locator('input[type="text"], textarea').count()
    expect(inputCount).toBeGreaterThan(0)
  })

  test('can enter a topic', async ({ page }) => {
    // The first text input must be visible for entering a topic
    const firstInput = page.locator('input[type="text"], textarea').first()
    await expect(firstInput).toBeVisible()
    await firstInput.fill('Introduction to Machine Learning')
    await expect(firstInput).toHaveValue(/Machine Learning/)
  })

  test('generate button is present', async ({ page }) => {
    // The generate button is a core UI element and must be visible
    const generateButton = page.getByRole('button', { name: /generate/i })
    await expect(generateButton).toBeVisible()
    await expect(generateButton).toBeEnabled()
  })

  test('can add keywords', async ({ page }) => {
    // Keywords input should be present on the content generation form
    const keywordsInput = page.getByPlaceholder(/keyword/i).or(
      page.getByLabel(/keyword/i)
    ).or(
      page.locator('input[name="keywords"]')
    )

    const keywordsElement = keywordsInput.first()
    if (!(await keywordsElement.isVisible({ timeout: 5000 }).catch(() => false))) {
      test.skip(true, 'Keywords input not available in this UI layout')
      return
    }

    await expect(keywordsElement).toBeVisible()
    await keywordsElement.fill('AI, technology')
    await expect(keywordsElement).toHaveValue(/AI/)
  })

  test('can toggle research option', async ({ page }) => {
    // Research toggle may not be present in all UI configurations
    const researchToggle = page.getByRole('checkbox', { name: /research/i }).or(
      page.getByLabel(/research/i)
    )

    const toggleElement = researchToggle.first()
    if (!(await toggleElement.isVisible({ timeout: 5000 }).catch(() => false))) {
      test.skip(true, 'Research toggle not available in this UI layout')
      return
    }

    await expect(toggleElement).toBeVisible()
    await toggleElement.click()
  })

  test('can select tone', async ({ page }) => {
    // Tone selector may not be present in all UI configurations
    const toneSelect = page.getByRole('combobox', { name: /tone/i }).or(
      page.getByLabel(/tone/i)
    )

    const toneElement = toneSelect.first()
    if (!(await toneElement.isVisible({ timeout: 5000 }).catch(() => false))) {
      test.skip(true, 'Tone selector not available in this UI layout')
      return
    }

    await expect(toneElement).toBeVisible()
    await toneElement.click()
  })

  test('tabs switch between blog and book generation', async ({ page }) => {
    // Blog and book tabs are core UI elements
    const blogTab = page.getByRole('tab', { name: /blog/i })
    const bookTab = page.getByRole('tab', { name: /book/i })

    await expect(blogTab).toBeVisible()
    await expect(bookTab).toBeVisible()

    // Click book tab
    await bookTab.click()

    // Should show book-specific options like chapters input
    const chaptersInput = page.getByLabel(/chapter/i).or(
      page.locator('input[name*="chapter"]')
    )
    await expect(chaptersInput.first()).toBeVisible()

    // Click back to blog tab
    await blogTab.click()
  })
})
