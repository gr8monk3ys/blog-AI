import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { render, waitFor } from '@testing-library/react'
import { ThemeProvider } from '../../hooks/useTheme'
import PricingPage from '../../app/pricing/PricingPageClient'
import { API_ENDPOINTS } from '../../lib/api'

/**
 * The visitor's current tier comes from an endpoint that needs a Clerk
 * session token. Asking for it before Clerk has loaded, or while signed out,
 * is a guaranteed 401 in the console, and for a signed-in visitor it also
 * meant the "Current Plan" marker never appeared.
 */
const auth = { configured: true, isLoaded: false, isSignedIn: false, unavailable: false }

vi.mock('../../lib/clerk-ui', () => ({
  isClerkConfigured: () => auth.configured,
  useAuth: () => ({ isLoaded: auth.isLoaded, isSignedIn: auth.isSignedIn, userId: null }),
  useClerkUnavailable: () => auth.unavailable,
  SignedIn: () => null,
  SignedOut: () => null,
  UserButton: () => null,
}))

const fetchMock = vi.fn(async () => new Response(JSON.stringify({}), { status: 200 }))
const tierRequests = () =>
  fetchMock.mock.calls.filter(([url]) => String(url) === API_ENDPOINTS.usage.stats).length

const renderPricing = () => render(<PricingPage initialTiers={[]} />, { wrapper: ThemeProvider })

beforeEach(() => {
  Object.assign(auth, { configured: true, isLoaded: false, isSignedIn: false, unavailable: false })
  fetchMock.mockClear()
  vi.stubGlobal('fetch', fetchMock)
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('PricingPage current tier', () => {
  it('waits for Clerk before asking', async () => {
    renderPricing()
    await waitFor(() => expect(fetchMock).toHaveBeenCalled())
    expect(tierRequests()).toBe(0)
  })

  it('does not ask for a signed-out visitor', async () => {
    auth.isLoaded = true
    renderPricing()
    await waitFor(() => expect(fetchMock).toHaveBeenCalled())
    expect(tierRequests()).toBe(0)
  })

  it('asks once a session is loaded', async () => {
    const { rerender } = renderPricing()
    Object.assign(auth, { isLoaded: true, isSignedIn: true })
    rerender(<PricingPage initialTiers={[]} />)
    await waitFor(() => expect(tierRequests()).toBe(1))
  })

  it('asks without a session when Clerk is not configured', async () => {
    Object.assign(auth, { configured: false, isLoaded: true })
    renderPricing()
    await waitFor(() => expect(tierRequests()).toBe(1))
  })
})
