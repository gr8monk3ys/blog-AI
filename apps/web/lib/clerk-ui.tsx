'use client'

import { useEffect, useState, type ReactNode } from 'react'
import {
  ClerkProvider as ClerkProviderImpl,
  SignedIn as SignedInImpl,
  SignedOut as SignedOutImpl,
  UserButton as UserButtonImpl,
  SignIn as SignInImpl,
  SignUp as SignUpImpl,
  useAuth as useAuthImpl,
} from '@clerk/nextjs'

type UseAuthResult = {
  isLoaded: boolean
  isSignedIn: boolean
  userId: string | null
}

export function isClerkConfigured(): boolean {
  return !!process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
}

/**
 * Grace period before a configured-but-silent Clerk is treated as unavailable.
 * Long enough to cover a slow script fetch, short enough that a visitor does
 * not stare at a hero with no buttons.
 */
const CLERK_LOAD_GRACE_MS = 4000

type ClerkGlobal = { loaded?: boolean; status?: string }

const readClerk = (): ClerkGlobal | undefined =>
  (globalThis as { Clerk?: ClerkGlobal }).Clerk

/**
 * Clerk is usable only once it reports `loaded`. Two distinct failures look
 * different on `window`:
 *   - script never arrives      -> window.Clerk is undefined
 *   - script arrives, init fails -> window.Clerk exists, loaded false, status 'error'
 * Only the first was obvious from production; the second showed up when this
 * was reproduced locally against a host that resolved but had no instance.
 */
const clerkIsReady = (): boolean => readClerk()?.loaded === true

const clerkHasFailed = (): boolean => readClerk()?.status === 'error'

/**
 * True when Clerk is configured but has not become ready in time.
 *
 * Clerk's <SignedIn> and <SignedOut> BOTH render nothing until the script
 * resolves. So when the frontend-api host is unreachable, every auth-gated
 * control disappears at once -- including the marketing CTAs, which are not
 * really auth UI at all. On 2026-09-08 the production site shipped a hero with
 * no buttons and a header with no sign-in link for exactly this reason:
 * clerk.lscaturchio.xyz accepted the TCP connection and then returned no bytes.
 *
 * Treating that state as "signed out" degrades to the correct page: a visitor
 * who cannot be identified is, for display purposes, a logged-out visitor.
 */
export function useClerkUnavailable(graceMs: number = CLERK_LOAD_GRACE_MS): boolean {
  const [unavailable, setUnavailable] = useState(false)

  useEffect(() => {
    if (!isClerkConfigured() || typeof window === 'undefined') return undefined

    if (clerkIsReady()) return undefined

    const poll = setInterval(() => {
      if (clerkIsReady()) {
        setUnavailable(false)
        clearInterval(poll)
        return
      }
      // A reported error will not resolve itself; do not make the visitor
      // wait out the rest of the grace period for it.
      if (clerkHasFailed()) {
        setUnavailable(true)
        clearInterval(poll)
      }
    }, 250)

    const timer = setTimeout(() => {
      if (!clerkIsReady()) setUnavailable(true)
    }, graceMs)

    return () => {
      clearInterval(poll)
      clearTimeout(timer)
    }
  }, [graceMs])

  return unavailable
}

export function ClerkProvider({
  children,
  publishableKey,
}: {
  children: ReactNode
  publishableKey: string
}): ReactNode {
  if (!isClerkConfigured()) {
    return children
  }

  return <ClerkProviderImpl publishableKey={publishableKey}>{children}</ClerkProviderImpl>
}

export function SignedIn({ children }: { children: ReactNode }): ReactNode {
  const clerkUnavailable = useClerkUnavailable()

  // With Clerk down we cannot prove anyone is signed in, so render nothing.
  // SignedOut is what fills the gap.
  if (!isClerkConfigured() || clerkUnavailable) {
    return null
  }

  return <SignedInImpl>{children}</SignedInImpl>
}

export function SignedOut({ children }: { children: ReactNode }): ReactNode {
  const clerkUnavailable = useClerkUnavailable()

  // Not configured, or configured and never loaded: show the signed-out view.
  if (!isClerkConfigured() || clerkUnavailable) {
    return children
  }

  return <SignedOutImpl>{children}</SignedOutImpl>
}

export function UserButton(props: Record<string, unknown>): ReactNode {
  if (!isClerkConfigured()) {
    return null
  }

  return <UserButtonImpl {...props} />
}

export function SignIn(props: Record<string, unknown>): ReactNode {
  if (!isClerkConfigured()) {
    return null
  }

  return <SignInImpl {...props} />
}

export function SignUp(props: Record<string, unknown>): ReactNode {
  if (!isClerkConfigured()) {
    return null
  }

  return <SignUpImpl {...props} />
}

export function useAuth(): UseAuthResult {
  let auth: ReturnType<typeof useAuthImpl> | null = null

  try {
    // This wrapper intentionally tolerates missing Clerk config and provider state.
    // eslint-disable-next-line react-hooks/rules-of-hooks
    auth = useAuthImpl()
  } catch {
    auth = null
  }

  if (!isClerkConfigured() || !auth) {
    return {
      isLoaded: true,
      isSignedIn: false,
      userId: null,
    }
  }

  return {
    isLoaded: auth.isLoaded,
    isSignedIn: !!auth.isSignedIn,
    userId: auth.userId ?? null,
  }
}
