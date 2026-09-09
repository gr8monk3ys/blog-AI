import { describe, it, expect, beforeEach, afterEach, afterAll, vi } from 'vitest'
import { render, screen, act } from '@testing-library/react'

// The real <SignedIn>/<SignedOut> render NOTHING until clerk.browser.js resolves.
// The global test setup mocks them as pass-throughs, which hides that behaviour,
// so this suite restores it: both render null, exactly as an unloaded Clerk does.
vi.mock('@clerk/nextjs', () => ({
  SignedIn: () => null,
  SignedOut: () => null,
  UserButton: () => null,
  SignIn: () => null,
  SignUp: () => null,
  useUser: () => ({ isSignedIn: false, user: null }),
  useAuth: () => ({ isLoaded: false, isSignedIn: false, userId: null }),
  ClerkProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  auth: () => ({ userId: null }),
}))

import { SignedIn, SignedOut } from '../../lib/clerk-ui'

/**
 * Regression: on 2026-09-08 blog-ai.vivancedata.com rendered a hero with no
 * buttons and a header with no sign-in link. clerk.lscaturchio.xyz accepted the
 * TCP connection and then returned no bytes, so clerk.browser.js never loaded.
 * Because <SignedIn> and <SignedOut> both render nothing until it does, every
 * CTA on the marketing page disappeared at once.
 */
describe('clerk-ui: Clerk configured but script never loads', () => {
  const originalKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY

  beforeEach(() => {
    vi.useFakeTimers()
    process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY = 'pk_test_mock'
    delete (window as Window & { Clerk?: unknown }).Clerk
  })

  afterEach(() => {
    vi.useRealTimers()
    delete (window as Window & { Clerk?: unknown }).Clerk
  })

  afterAll(() => {
    if (originalKey) process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY = originalKey
    else delete process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
  })

  it('renders nothing before the grace period elapses', () => {
    render(
      <SignedOut>
        <span data-testid="cta">Start Free</span>
      </SignedOut>
    )

    act(() => {
      vi.advanceTimersByTime(1000)
    })

    // Still inside the grace period: Clerk may yet load, so defer to it.
    expect(screen.queryByTestId('cta')).not.toBeInTheDocument()
  })

  it('falls back to the signed-out CTAs once the grace period elapses', () => {
    render(
      <SignedOut>
        <span data-testid="cta">Start Free</span>
      </SignedOut>
    )

    act(() => {
      vi.advanceTimersByTime(5000)
    })

    expect(screen.getByTestId('cta')).toBeInTheDocument()
  })

  it('never claims the visitor is signed in when Clerk is unavailable', () => {
    render(
      <SignedIn>
        <span data-testid="app-link">Start Generating</span>
      </SignedIn>
    )

    act(() => {
      vi.advanceTimersByTime(5000)
    })

    expect(screen.queryByTestId('app-link')).not.toBeInTheDocument()
  })

  it('defers to Clerk when the script loads successfully', () => {
    ;(window as Window & { Clerk?: unknown }).Clerk = { loaded: true, status: 'ready' }

    render(
      <SignedOut>
        <span data-testid="cta">Start Free</span>
      </SignedOut>
    )

    act(() => {
      vi.advanceTimersByTime(5000)
    })

    // Clerk is present, so the real <SignedOut> decides; here it renders null.
    // Proves the fallback does not fire once Clerk is up.
    expect(screen.queryByTestId('cta')).not.toBeInTheDocument()
  })

  it('falls back when the Clerk script loads but fails to initialise', () => {
    // Reproduced locally: the host resolved, clerk.browser.js executed, and
    // Clerk then reported status "error". window.Clerk exists but is never
    // ready, so an existence check would wrongly conclude Clerk is fine.
    ;(window as Window & { Clerk?: unknown }).Clerk = { loaded: false, status: 'error' }

    render(
      <SignedOut>
        <span data-testid="cta">Start Free</span>
      </SignedOut>
    )

    act(() => {
      vi.advanceTimersByTime(500)
    })

    // Resolved on the poll, without waiting out the full grace period.
    expect(screen.getByTestId('cta')).toBeInTheDocument()
  })

  it('recovers silently when Clerk becomes ready during the grace period', () => {
    render(
      <SignedOut>
        <span data-testid="cta">Start Free</span>
      </SignedOut>
    )

    act(() => {
      vi.advanceTimersByTime(1000)
    })
    ;(window as Window & { Clerk?: unknown }).Clerk = { loaded: true, status: 'ready' }
    act(() => {
      vi.advanceTimersByTime(5000)
    })

    // Clerk is in charge again; the mocked <SignedOut> renders nothing.
    expect(screen.queryByTestId('cta')).not.toBeInTheDocument()
  })
})
