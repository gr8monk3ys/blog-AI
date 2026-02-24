import { expect, type Page } from '@playwright/test'

function loadingLocator(page: Page) {
  return page.getByRole('status', { name: /loading/i }).first()
}

export function authPromptLocator(page: Page) {
  return page
    .getByText(/clerk is not configured/i)
    .or(page.getByRole('heading', { name: /sign in/i }))
    .or(page.getByRole('button', { name: /sign in|continue/i }))
    .or(page.getByText(/enable sign-in/i))
    .first()
}

export async function waitForAppToSettle(page: Page): Promise<void> {
  await page.waitForLoadState('domcontentloaded')
  await page.waitForLoadState('networkidle', { timeout: 10_000 }).catch(() => undefined)

  const loading = loadingLocator(page)
  if ((await loading.count()) > 0) {
    await loading.waitFor({ state: 'hidden', timeout: 30_000 }).catch(() => undefined)
  }
}

export async function isAuthPromptVisible(page: Page): Promise<boolean> {
  return authPromptLocator(page).isVisible({ timeout: 2_000 }).catch(() => false)
}

export async function resolveProtectedRouteState(
  page: Page,
  routePattern: RegExp
): Promise<'protected' | 'auth'> {
  await waitForAppToSettle(page)

  const currentUrl = page.url()
  const pathname = new URL(currentUrl).pathname

  if (routePattern.test(pathname)) {
    return 'protected'
  }

  if (/^\/(sign-in|auth)(\/|$)/.test(pathname)) {
    return 'auth'
  }

  if (await isAuthPromptVisible(page)) {
    return 'auth'
  }

  await expect(page).toHaveURL(routePattern)
  return 'protected'
}
