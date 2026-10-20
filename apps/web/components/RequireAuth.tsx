'use client'

import Link from 'next/link'
import { useAuth } from '../lib/clerk-ui'
import { buttonVariants } from './ui/Button'

interface RequireAuthProps {
  /** Content to render when the user is authenticated. */
  children: React.ReactNode
  /**
   * Where to redirect unauthenticated users.
   * Defaults to `/sign-in`.
   */
  redirectTo?: string
  /**
   * Optional loading indicator shown while Clerk is still loading.
   * When omitted a minimal branded spinner is rendered.
   */
  fallback?: React.ReactNode
}

/**
 * Client-side auth gate that redirects unauthenticated visitors to the
 * sign-in page. Use this as a defense-in-depth wrapper inside pages that
 * are already protected by middleware -- it handles the edge case where
 * middleware is bypassed or not yet applied (e.g. client-side navigations
 * that skip the middleware layer).
 *
 * The gate renders inside the app shell's <main>, so its two interim states
 * are plain blocks, not landmarks.
 *
 * Usage:
 * ```tsx
 * <RequireAuth>
 *   <MyProtectedContent />
 * </RequireAuth>
 * ```
 */
export default function RequireAuth({
  children,
  redirectTo = '/sign-in',
  fallback,
}: RequireAuthProps): React.ReactElement | null {
  const { isLoaded, isSignedIn } = useAuth()

  // Clerk is still initializing -- show a loading state.
  if (!isLoaded) {
    if (fallback) {
      return <>{fallback}</>
    }

    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <div className="flex items-center gap-3" role="status" aria-label="Loading">
          <div className="h-2.5 w-2.5 animate-pulse rounded-full bg-primary/40" />
          <div
            className="h-2.5 w-2.5 animate-pulse rounded-full bg-primary/70"
            style={{ animationDelay: '150ms' }}
          />
          <div
            className="h-2.5 w-2.5 animate-pulse rounded-full bg-primary"
            style={{ animationDelay: '300ms' }}
          />
        </div>
      </div>
    )
  }

  // User is not signed in.
  if (!isSignedIn) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center px-4">
        <div className="max-w-sm text-center">
          <p className="label-mono">Account</p>
          <p className="mt-3 mb-6 text-sm text-muted-foreground">
            You need to sign in to view this page.
          </p>
          <Link href={redirectTo} className={buttonVariants()}>
            Sign In
          </Link>
        </div>
      </div>
    )
  }

  return <>{children}</>
}
