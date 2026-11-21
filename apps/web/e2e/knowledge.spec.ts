import { test, expect } from '@playwright/test'

test.describe('Knowledge Base page', () => {
  test('sends a signed-out visitor to sign-in and back', async ({ page }) => {
    await page.goto('/knowledge')
    await expect(page).toHaveURL(/\/sign-in\?redirect=%2Fknowledge$/)
  })

  test('hides the Knowledge Base nav link when the feature flag is off', async ({
    page,
  }) => {
    // The Knowledge Base backend ships flagged off (ENABLE_KNOWLEDGE_BASE=false),
    // so the nav link is gated behind NEXT_PUBLIC_ENABLE_KNOWLEDGE_BASE, which is
    // unset in the E2E environment. The header should not advertise the route.
    await page.goto('/')
    await expect(
      page.getByRole('link', { name: /knowledge base/i })
    ).toHaveCount(0)
  })
})

test.describe('Blog generator KB toggle', () => {
  // The "Use Knowledge Base" toggle lives in the content-generator advanced
  // options, which only render on the auth-gated /generate and tool-detail
  // pages. In the unauthenticated E2E environment /tools redirects
  // to /sign-in, so this assertion is unreachable as written. Re-enable once
  // E2E runs with an authenticated session (tracked in docs/SCHEMA_AUDIT.md).
  test.fixme('should show Use Knowledge Base toggle in advanced options', async ({
    page,
  }) => {
    await page.goto('/tools')
    // The toggle should be present in the form
    await expect(page.getByText(/use knowledge base/i)).toBeVisible()
  })
})
