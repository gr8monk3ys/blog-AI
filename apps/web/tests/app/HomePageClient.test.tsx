import { describe, it, expect, beforeAll, beforeEach, afterAll, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ThemeProvider } from '../../hooks/useTheme'
import Home from '../../app/HomePageClient'

/**
 * The hero CTA must never disappear.
 *
 * Clerk's <SignedIn>/<SignedOut> both render nothing until clerk.browser.js has
 * loaded — and forever if it fails to load (a blocked script, a misconfigured
 * custom domain). That left the homepage with a headline, a subhead, an empty
 * gap where the buttons belong, and a "No credit card required" line pointing
 * at nothing. These tests pin the unauthenticated CTA to the "not yet loaded"
 * state so the primary action never depends on a third-party script.
 */
const authState = {
  isLoaded: false,
  isSignedIn: false,
  userId: null as string | null,
}

vi.mock('../../lib/clerk-ui', () => ({
  isClerkConfigured: () => true,
  useAuth: () => authState,
  // SiteHeader/SiteFooter render inside the page; mirror Clerk's real
  // behaviour, where both gates render nothing until the script has loaded.
  SignedIn: () => null,
  SignedOut: () => null,
  UserButton: () => null,
}))

function renderHome() {
  return render(<Home />, { wrapper: ThemeProvider })
}

const originalClerkKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY

beforeAll(() => {
  process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY = 'pk_test_dummy'

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

afterAll(() => {
  if (originalClerkKey) {
    process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY = originalClerkKey
  } else {
    delete process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
  }
})

beforeEach(() => {
  authState.isLoaded = false
  authState.isSignedIn = false
  authState.userId = null
})

describe('HomePageClient hero CTA', () => {
  it('renders the signed-out CTA while Clerk is still loading', () => {
    renderHome()

    const startFree = screen.getAllByRole('link', { name: /start free/i })
    expect(startFree.length).toBeGreaterThan(0)
    expect(startFree[0]).toHaveAttribute('href', '/sign-up')
    expect(screen.getByRole('link', { name: /view plans/i })).toHaveAttribute(
      'href',
      '/pricing'
    )
  })

  it('still renders the signed-out CTA when Clerk loads with no session', () => {
    authState.isLoaded = true

    renderHome()

    expect(screen.getByRole('link', { name: /view plans/i })).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /start generating/i })).toBeNull()
  })

  it('swaps to the authenticated CTA once Clerk reports a session', () => {
    authState.isLoaded = true
    authState.isSignedIn = true
    authState.userId = 'user_test'

    renderHome()

    expect(
      screen.getAllByRole('link', { name: /start generating/i })[0]
    ).toHaveAttribute('href', '/generate')
    // "View Plans" is unique to the signed-out hero (the pricing section keeps
    // its own "Start Free" tier button, so that label is not a hero signal).
    expect(screen.queryByRole('link', { name: /view plans/i })).toBeNull()
  })
})
