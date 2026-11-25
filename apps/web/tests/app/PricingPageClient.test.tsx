import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { render, screen, waitFor, within } from '@testing-library/react'
import { ThemeProvider } from '../../hooks/useTheme'
import PricingPage from '../../app/pricing/PricingPageClient'
import { API_ENDPOINTS } from '../../lib/api'
import { sessionState, signedInSession } from '../auth-mock'

/**
 * The visitor's current tier comes from an endpoint that needs an API token.
 * Asking for it before the session has loaded, or while signed out, is a
 * guaranteed 401 in the console, and for a signed-in visitor it also meant
 * the "Current Plan" marker never appeared.
 */
const fetchMock = vi.fn(async () => new Response(JSON.stringify({}), { status: 200 }))
const tierRequests = () =>
  fetchMock.mock.calls.filter(([url]) => String(url) === API_ENDPOINTS.usage.stats).length

const renderPricing = () => render(<PricingPage initialTiers={[]} />, { wrapper: ThemeProvider })

beforeEach(() => {
  Object.assign(sessionState, { data: null, isPending: true })
  fetchMock.mockClear()
  vi.stubGlobal('fetch', fetchMock)
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('PricingPage current tier', () => {
  it('waits for the session before asking', async () => {
    renderPricing()
    await waitFor(() => expect(fetchMock).toHaveBeenCalled())
    expect(tierRequests()).toBe(0)
  })

  it('does not ask for a signed-out visitor', async () => {
    sessionState.isPending = false
    renderPricing()
    await waitFor(() => expect(fetchMock).toHaveBeenCalled())
    expect(tierRequests()).toBe(0)
  })

  it('asks once a session is loaded', async () => {
    const { rerender } = renderPricing()
    Object.assign(sessionState, { data: signedInSession, isPending: false })
    rerender(<PricingPage initialTiers={[]} />)
    await waitFor(() => expect(tierRequests()).toBe(1))
  })

})

/**
 * Without Stripe price ids the API still lists the paid plans, just without
 * `stripe_price_id_*`. The card must say checkout is unavailable instead of
 * offering a button that can only fail.
 */
describe('PricingPage checkout availability', () => {
  const starter = {
    id: 'starter' as const,
    name: 'Starter',
    price_monthly: 19,
    price_yearly: 190,
    features: ['50 generations per month'],
  }

  const servePricing = (tiers: unknown[]) =>
    fetchMock.mockImplementation(async (url: unknown) =>
      String(url) === API_ENDPOINTS.payments.pricing
        ? new Response(JSON.stringify({ success: true, tiers }), { status: 200 })
        : new Response(JSON.stringify({}), { status: 200 })
    )

  const starterCard = () =>
    screen.getByRole('heading', { level: 2, name: 'Starter' }).closest('div.flex-col') as HTMLElement

  beforeEach(() => {
    Object.assign(sessionState, { data: signedInSession, isPending: false })
  })

  afterEach(() => {
    fetchMock.mockImplementation(async () => new Response(JSON.stringify({}), { status: 200 }))
  })

  it('shows checkout unavailable when the plan has no Stripe price', async () => {
    servePricing([starter])
    render(<PricingPage initialTiers={[starter]} />, { wrapper: ThemeProvider })

    const button = await within(starterCard()).findByRole('button', { name: 'Checkout unavailable' })
    expect(button).toBeDisabled()
    expect(within(starterCard()).getByText(/online checkout is not set up for this plan yet/i)).toBeInTheDocument()
  })

  it('offers checkout when the plan has a Stripe price', async () => {
    servePricing([{ ...starter, stripe_price_id_monthly: 'price_m', stripe_price_id_yearly: 'price_y' }])
    render(<PricingPage initialTiers={[starter]} />, { wrapper: ThemeProvider })

    const button = await within(starterCard()).findByRole('button', { name: 'Choose Starter' })
    expect(button).toBeEnabled()
    expect(within(starterCard()).queryByText(/checkout unavailable/i)).toBeNull()
  })
})

describe('PricingPage comparison table', () => {
  const tier = (features: string[]) => ({
    id: 'starter' as const,
    name: 'Starter',
    price_monthly: 19,
    price_yearly: 190,
    features,
  })

  it('leaves out research mode when no plan lists it', () => {
    render(<PricingPage initialTiers={[tier(['Priority support'])]} />, { wrapper: ThemeProvider })
    expect(screen.queryByRole('rowheader', { name: 'Research mode' })).toBeNull()
  })

  it('compares research mode when a plan lists it', () => {
    render(<PricingPage initialTiers={[tier(['Research mode'])]} />, { wrapper: ThemeProvider })
    expect(screen.getByRole('rowheader', { name: 'Research mode' })).toBeInTheDocument()
  })
})
