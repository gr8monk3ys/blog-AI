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

    // At least one of these must be present
    const profileCount = await profileCards.count()
    const emptyCount = await emptyState.count()
    const buttonCount = await createButton.count()
    expect(profileCount + emptyCount + buttonCount).toBeGreaterThan(0)
  })

  test('create profile button is present', async ({ page }) => {
    // The create button is a core UI element on the brand page
    const createButton = page.getByRole('button', { name: /create|add|new/i })
    await expect(createButton.first()).toBeVisible()
  })

  test('can open create profile modal', async ({ page }) => {
    // The create button must be present to open the modal
    const createButton = page.getByRole('button', { name: /create|add|new/i })
    await expect(createButton.first()).toBeVisible()
    await createButton.first().click()

    // Modal or form must appear after clicking create
    const modal = page.getByRole('dialog').or(
      page.locator('[role="dialog"]')
    ).or(
      page.locator('.modal')
    )

    const form = page.getByRole('form').or(
      page.locator('form')
    )

    // Either modal or form must appear
    const modalCount = await modal.count()
    const formCount = await form.count()
    expect(modalCount + formCount).toBeGreaterThan(0)

    // Form name input must be present
    const nameInput = page.getByLabel(/name/i).or(
      page.getByPlaceholder(/name/i)
    )
    await expect(nameInput.first()).toBeVisible()
  })

  test('profile cards are clickable', async ({ page }) => {
    // Profile cards only exist when profiles have been created
    const profileCards = page.locator('[data-testid="profile-card"]').or(
      page.locator('.profile-card')
    ).or(
      page.locator('article')
    )

    if (\!(await profileCards.first().isVisible({ timeout: 5000 }).catch(() => false))) {
      test.skip(true, 'No profile cards available -- no profiles have been created')
      return
    }

    const firstCard = profileCards.first()
    await expect(firstCard).toBeVisible()

    // Check if it is clickable (has click handler or is a link)
    const tagName = await firstCard.evaluate(el => el.tagName.toLowerCase())
    if (tagName === 'a' || tagName === 'button') {
      await firstCard.click()
    }
  })
})
