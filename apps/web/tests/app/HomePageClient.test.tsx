import { describe, it, expect, beforeAll, beforeEach, afterEach, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ThemeProvider } from '../../hooks/useTheme'
import Home from '../../app/HomePageClient'
import { sessionState, signedInSession } from '../auth-mock'

/**
 * The hero CTA must never disappear: the signed-out CTA renders until the
 * session positively loads, so the primary action is in the first paint.
 */
function renderHome() {
  return render(<Home />, { wrapper: ThemeProvider })
}

beforeAll(() => {
  if (!('IntersectionObserver' in globalThis)) {
    class MockIntersectionObserver {
      observe(): void {}
      unobserve(): void {}
      disconnect(): void {}
      takeRecords(): [] {
        return []
      }
    }
    Object.defineProperty(globalThis, 'IntersectionObserver', {
      writable: true,
      value: MockIntersectionObserver,
    })
  }
})

beforeEach(() => {
  sessionState.data = null
  sessionState.isPending = true
})

describe('HomePageClient hero CTA', () => {
  it('renders the signed-out CTA while the session is loading', () => {
    renderHome()

    const startFree = screen.getAllByRole('link', { name: /start free/i })
    expect(startFree.length).toBeGreaterThan(0)
    expect(startFree[0]).toHaveAttribute('href', '/sign-up')
    expect(screen.getByRole('link', { name: /view plans/i })).toHaveAttribute(
      'href',
      '/pricing'
    )
  })

  it('still renders the signed-out CTA when the session loads empty', () => {
    sessionState.isPending = false

    renderHome()

    expect(screen.getByRole('link', { name: /view plans/i })).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /start generating/i })).toBeNull()
  })

  it('swaps to the authenticated CTA once a session loads', () => {
    sessionState.isPending = false
    sessionState.data = signedInSession

    renderHome()

    expect(
      screen.getAllByRole('link', { name: /start generating/i })[0]
    ).toHaveAttribute('href', '/generate')
    // "View Plans" is unique to the signed-out hero (the pricing section keeps
    // its own "Start Free" tier button, so that label is not a hero signal).
    expect(screen.queryByRole('link', { name: /view plans/i })).toBeNull()
  })
})

describe('HomePageClient plans ledger', () => {
  afterEach(() => {
    vi.unstubAllEnvs()
  })

  it('does not sell research while web research is off', () => {
    vi.stubEnv('NEXT_PUBLIC_FEATURE_WEB_RESEARCH', '')
    renderHome()
    expect(screen.queryByText('Research mode')).toBeNull()
    expect(screen.queryByText('Fact-checking')).toBeNull()
  })

  it('lists research once web research is on', () => {
    vi.stubEnv('NEXT_PUBLIC_FEATURE_WEB_RESEARCH', 'true')
    renderHome()
    expect(screen.getByText('Research mode')).toBeInTheDocument()
  })
})
