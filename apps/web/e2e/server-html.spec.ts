import { test, expect } from '@playwright/test'

// React marks a Suspense boundary that was still waiting when the HTML was
// sent with `<!--$?-->`: the browser shows its fallback first and the real
// content is swapped in by script afterwards. Public pages have nothing to
// wait for, so their headline must be in the HTML as sent.
const PUBLIC_PAGES = ['/', '/pricing', '/blog', '/tools', '/tool-directory', '/privacy', '/terms']

test.describe('Server HTML of public pages', () => {
  for (const path of PUBLIC_PAGES) {
    test(`${path} is sent complete, with no pending Suspense boundary`, async ({ request }) => {
      const html = await (await request.get(path)).text()

      expect(html).toContain('<h1')
      expect(
        html,
        `${path} was sent behind a Suspense fallback. Remove the loading.tsx or <Suspense> above the page content, or move it down around the part that really waits.`
      ).not.toContain('<!--$?-->')
    })
  }
})
