'use client'

import Link from 'next/link'
import { useAuth } from '@clerk/nextjs'

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
      <main className="min-h-screen flex items-center justify-center">
        <div className="flex items-center gap-3" role="status" aria-label="Loading">
          <div className="h-2.5 w-2.5 rounded-full bg-amber-400 animate-bounce" />
          <div
            className="h-2.5 w-2.5 rounded-full bg-amber-500 animate-bounce"
            style={{ animationDelay: '150ms' }}
          />
          <div
            className="h-2.5 w-2.5 rounded-full bg-amber-600 animate-bounce"
            style={{ animationDelay: '300ms' }}
          />
        </div>
      </main>
    )
  }

  // User is not signed in.
  if (!isSignedIn) {
    return (
      <main className="min-h-screen flex items-center justify-center px-4">
        <div className="text-center max-w-sm">
          <p className="text-sm text-gray-600 mb-4">
            You need to sign in to view this page.
          </p>
          <Link
            href={redirectTo}
            className="inline-flex items-center px-4 py-2 rounded-lg bg-amber-600 text-white text-sm font-medium hover:bg-amber-700 transition-colors"
          >
            Sign In
          </Link>
        </div>
      </main>
    )
  }

  return <>{children}</>
}
