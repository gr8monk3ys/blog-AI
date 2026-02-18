'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
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
  const router = useRouter()

  useEffect(() => {
    if (isLoaded && !isSignedIn) {
      router.replace(redirectTo)
    }
  }, [isLoaded, isSignedIn, redirectTo, router])

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

  // User is not signed in -- redirect is already in progress via the effect.
  if (!isSignedIn) {
    return null
  }

  return <>{children}</>
}
