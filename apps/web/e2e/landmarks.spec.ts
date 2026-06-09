import { test, expect } from '@playwright/test'

/**
 * Landmark regression guard.
 *
 * SiteHeader/SiteFooter must be siblings of <main>, not children: a <header>
 * nested inside <main> loses its implicit `banner` role (same for <footer> /
 * `contentinfo`), which breaks assistive-tech navigation. This swept the whole
 * app once; these checks keep the public pages honest.
 */
// Limited to pages already exercised by the E2E suite (render reliably in the
// no-backend E2E environment); the underlying fix was applied to all 16 pages.
const PUBLIC_PAGES = ['/', '/pricing']

for (const path of PUBLIC_PAGES) {
  test(`page ${path} exposes banner and contentinfo landmarks`, async ({
    page,
  }) => {
    await page.goto(path)
    await expect(page.getByRole('banner')).toBeVisible()
    await expect(page.getByRole('contentinfo')).toBeVisible()
  })
}
