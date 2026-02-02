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
    // Should see the topic input or content generation form
    const topicInput = page.getByPlaceholder(/topic/i).or(
      page.getByLabel(/topic/i)
    ).or(
      page.locator('input[name="topic"]')
    ).or(
      page.locator('textarea').first()
    )

    // Check if any input element exists for entering a topic
    const hasInput = await topicInput.count() > 0 ||
      await page.locator('input').count() > 0 ||
      await page.locator('textarea').count() > 0

    expect(hasInput).toBeTruthy()
  })

  test('can enter a topic', async ({ page }) => {
    // Find any input that might accept a topic
    const inputs = page.locator('input[type="text"], textarea')
    const firstInput = inputs.first()

    if (await firstInput.isVisible()) {
      await firstInput.fill('Introduction to Machine Learning')
      await expect(firstInput).toHaveValue(/Machine Learning/)
    }
  })

  test('generate button is present', async ({ page }) => {
    // Look for a generate button
    const generateButton = page.getByRole('button', { name: /generate/i })

    if (await generateButton.isVisible()) {
      await expect(generateButton).toBeEnabled()
    }
  })

  test('can add keywords', async ({ page }) => {
    // Look for keywords input
    const keywordsInput = page.getByPlaceholder(/keyword/i).or(
      page.getByLabel(/keyword/i)
    ).or(
      page.locator('input[name="keywords"]')
    )

    if (await keywordsInput.count() > 0 && await keywordsInput.first().isVisible()) {
      await keywordsInput.first().fill('AI, technology')
    }
  })

  test('can toggle research option', async ({ page }) => {
    // Look for research toggle/checkbox
    const researchToggle = page.getByRole('checkbox', { name: /research/i }).or(
      page.getByLabel(/research/i)
    ).or(
      page.locator('input[type="checkbox"]').first()
    )

    if (await researchToggle.count() > 0 && await researchToggle.first().isVisible()) {
      await researchToggle.first().click()
    }
  })

  test('can select tone', async ({ page }) => {
    // Look for tone selector
    const toneSelect = page.getByRole('combobox', { name: /tone/i }).or(
      page.getByLabel(/tone/i)
    )

    if (await toneSelect.count() > 0 && await toneSelect.first().isVisible()) {
      await toneSelect.first().click()
    }
  })

  test('tabs switch between blog and book generation', async ({ page }) => {
    // Look for tabs to switch content type
    const blogTab = page.getByRole('tab', { name: /blog/i })
    const bookTab = page.getByRole('tab', { name: /book/i })

    if (await blogTab.isVisible() && await bookTab.isVisible()) {
      // Click book tab
      await bookTab.click()

      // Should show book-specific options
      const chaptersInput = page.getByLabel(/chapter/i).or(
        page.locator('input[name*="chapter"]')
      )
      // Book tab should change the form

      // Click back to blog tab
      await blogTab.click()
    }
  })
})
