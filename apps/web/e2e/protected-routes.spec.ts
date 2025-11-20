import { test, expect } from '@playwright/test'
import { resolveProtectedRouteState } from './helpers'

/**
 * E2E smoke tests for protected routes (templates, remix, onboarding, tools).
 *
 * These routes require authentication. Without valid credentials the server
 * redirects to sign-in. We verify the route either renders the protected
 * content or correctly redirects to the auth page.
 */
test.describe('Protected Routes', () => {
  test('templates route responds and redirects to auth or renders', async ({
    page,
  }) => {
    const response = await page.goto('/templates')

    expect(response?.status()).toBeLessThan(500)

    const state = await resolveProtectedRouteState(page, /\/templates/)
    expect(['protected', 'auth']).toContain(state)
  })

  test('remix route responds and redirects to auth or renders', async ({
    page,
  }) => {
    const response = await page.goto('/remix')

    expect(response?.status()).toBeLessThan(500)

    const state = await resolveProtectedRouteState(page, /\/remix/)
    expect(['protected', 'auth']).toContain(state)
  })

  test('onboarding route responds and redirects to auth or renders', async ({
    page,
  }) => {
    const response = await page.goto('/onboarding')

    expect(response?.status()).toBeLessThan(500)

    const state = await resolveProtectedRouteState(page, /\/onboarding/)
    expect(['protected', 'auth']).toContain(state)
  })

  test('tools route responds and redirects to auth or renders', async ({
    page,
  }) => {
    const response = await page.goto('/tools')

    expect(response?.status()).toBeLessThan(500)

    const state = await resolveProtectedRouteState(page, /\/tools/)
    expect(['protected', 'auth']).toContain(state)
  })

  test('bulk route responds and redirects to auth or renders', async ({
    page,
  }) => {
    const response = await page.goto('/bulk')

    expect(response?.status()).toBeLessThan(500)

    const state = await resolveProtectedRouteState(page, /\/bulk/)
    expect(['protected', 'auth']).toContain(state)
  })

  test('team route responds and redirects to auth or renders', async ({
    page,
  }) => {
    const response = await page.goto('/team')

    expect(response?.status()).toBeLessThan(500)

    const state = await resolveProtectedRouteState(page, /\/team/)
    expect(['protected', 'auth']).toContain(state)
  })
})
