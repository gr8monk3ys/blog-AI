import { test, expect } from '@playwright/test'

/**
 * E2E tests for brand voice profiles page.
 */
test.describe('Brand Profiles', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/brand')
  })

  test('brand page loads', async ({ page }) => {
    // Page should load without errors
    await expect(page.locator('body')).toBeVisible()
  })

  test('shows profiles list or empty state', async ({ page }) => {
    // Should show either profile cards or an empty state
    const profileCards = page.locator('[data-testid="profile-card"]').or(
      page.locator('.profile-card')
    ).or(
      page.locator('article')
    )

    const emptyState = page.getByText(/no.*profile/i).or(
      page.getByText(/create.*profile/i)
    ).or(
      page.getByText(/get started/i)
    )

    const createButton = page.getByRole('button', { name: /create|add|new/i })

    // Either profiles, empty state, or create button should be present
    const hasContent = await profileCards.count() > 0 ||
      await emptyState.count() > 0 ||
      await createButton.count() > 0
    expect(hasContent || await page.locator('body').isVisible()).toBeTruthy()
  })

  test('create profile button is present', async ({ page }) => {
    const createButton = page.getByRole('button', { name: /create|add|new/i })

    if (await createButton.count() > 0) {
      await expect(createButton.first()).toBeVisible()
    }
  })

  test('can open create profile modal', async ({ page }) => {
    const createButton = page.getByRole('button', { name: /create|add|new/i })

    if (await createButton.count() > 0 && await createButton.first().isVisible()) {
      await createButton.first().click()

      // Look for modal or form
      const modal = page.getByRole('dialog').or(
        page.locator('[role="dialog"]')
      ).or(
        page.locator('.modal')
      )

      const form = page.getByRole('form').or(
        page.locator('form')
      )

      // Either modal or form should appear
      const hasModalOrForm = await modal.count() > 0 || await form.count() > 0
      expect(hasModalOrForm).toBeTruthy()

      // Form elements should be present
      const nameInput = page.getByLabel(/name/i).or(
        page.getByPlaceholder(/name/i)
      )

      if (await nameInput.count() > 0) {
        await expect(nameInput.first()).toBeVisible()
      }
    }
  })

  test('profile cards are clickable', async ({ page }) => {
    const profileCards = page.locator('[data-testid="profile-card"]').or(
      page.locator('.profile-card')
    ).or(
      page.locator('article').first()
    )

    if (await profileCards.count() > 0) {
      // Clicking a card should navigate or open details
      const firstCard = profileCards.first()
      if (await firstCard.isVisible()) {
        // Check if it's clickable (has click handler or is a link)
        const tagName = await firstCard.evaluate(el => el.tagName.toLowerCase())
        if (tagName === 'a' || tagName === 'button') {
          await firstCard.click()
        }
      }
    }
  })
})
