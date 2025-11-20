import { describe, it, expect, beforeEach, afterAll, vi } from 'vitest'
import { render, screen, renderHook } from '@testing-library/react'
import * as clerkNext from '@clerk/nextjs'

import {
  ClerkProvider,
  SignedIn,
  SignedOut,
  SignIn,
  SignUp,
  UserButton,
  isClerkConfigured,
  useAuth,
} from '../../lib/clerk-ui'

describe('clerk-ui', () => {
  const originalClerkKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY

  beforeEach(() => {
    vi.restoreAllMocks()
    delete process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
  })

  afterAll(() => {
    if (originalClerkKey) {
      process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY = originalClerkKey
    } else {
      delete process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
    }
  })

  it('returns fallback UI when Clerk is not configured', () => {
    expect(isClerkConfigured()).toBe(false)

    const { rerender } = render(
      <ClerkProvider publishableKey="pk_test_mock">
        <div data-testid="provider-child" />
      </ClerkProvider>
    )
    expect(screen.getByTestId('provider-child')).toBeInTheDocument()

    rerender(<SignedIn><div data-testid="signed-in" /></SignedIn>)
    expect(screen.queryByTestId('signed-in')).not.toBeInTheDocument()

    rerender(<SignedOut><div data-testid="signed-out" /></SignedOut>)
    expect(screen.getByTestId('signed-out')).toBeInTheDocument()

    rerender(<UserButton />)
    expect(screen.queryByTestId('clerk-user-button')).not.toBeInTheDocument()

    rerender(<SignIn />)
    expect(screen.queryByTestId('clerk-sign-in')).not.toBeInTheDocument()

    rerender(<SignUp />)
    expect(screen.queryByTestId('clerk-sign-up')).not.toBeInTheDocument()

    const { result } = renderHook(() => useAuth())
    expect(result.current).toEqual({
      isLoaded: true,
      isSignedIn: false,
      userId: null,
    })
  })

  it('delegates to Clerk components and auth hook when configured', () => {
    process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY = 'pk_test_mock'

    vi.spyOn(clerkNext, 'useAuth').mockReturnValue({
      isLoaded: false,
      isSignedIn: true,
      userId: 'user_123',
      getToken: vi.fn(),
      orgId: null,
      orgRole: null,
      orgSlug: null,
      has: vi.fn(),
      signOut: vi.fn(),
      sessionId: null,
      actor: null,
    } as never)

    expect(isClerkConfigured()).toBe(true)

    const { rerender } = render(
      <ClerkProvider publishableKey="pk_test_mock">
        <div data-testid="provider-child" />
      </ClerkProvider>
    )
    expect(screen.getByTestId('provider-child')).toBeInTheDocument()

    rerender(<SignedIn><div data-testid="signed-in" /></SignedIn>)
    expect(screen.getByTestId('signed-in')).toBeInTheDocument()

    rerender(<SignedOut><div data-testid="signed-out" /></SignedOut>)
    expect(screen.getByTestId('signed-out')).toBeInTheDocument()

    rerender(<UserButton afterSignOutUrl="/" />)
    expect(screen.getByTestId('clerk-user-button')).toBeInTheDocument()

    rerender(<SignIn routing="path" />)
    expect(screen.getByTestId('clerk-sign-in')).toBeInTheDocument()

    rerender(<SignUp routing="path" />)
    expect(screen.getByTestId('clerk-sign-up')).toBeInTheDocument()

    const { result } = renderHook(() => useAuth())
    expect(result.current).toEqual({
      isLoaded: false,
      isSignedIn: true,
      userId: 'user_123',
    })
  })

  it('returns a safe fallback when Clerk throws during auth access', () => {
    process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY = 'pk_test_mock'
    vi.spyOn(clerkNext, 'useAuth').mockImplementation(() => {
      throw new Error('missing provider')
    })

    const { result } = renderHook(() => useAuth())

    expect(result.current).toEqual({
      isLoaded: true,
      isSignedIn: false,
      userId: null,
    })
  })
})
