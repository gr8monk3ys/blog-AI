'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import OnboardingWizard from '../../components/onboarding/OnboardingWizard'
import { hasCompletedOnboarding } from '../../lib/onboarding'
import RequireAuth from '../../components/RequireAuth'

/* -------------------------------------------------------------------------- */
/*  Clerk user helper                                                          */
/* -------------------------------------------------------------------------- */

interface ClerkGlobal {
  user?: { firstName?: string; lastName?: string }
  loaded?: boolean
}

function getClerkGlobal(): ClerkGlobal | undefined {
  if (typeof window === 'undefined') return undefined
  return (window as unknown as Record<string, unknown>).Clerk as
    | ClerkGlobal
    | undefined
}

function formatClerkName(clerk: ClerkGlobal | undefined): string {
  if (!clerk?.user) return ''
  const first = clerk.user.firstName || ''
  const last = clerk.user.lastName || ''
  return first ? `${first}${last ? ` ${last}` : ''}` : ''
}

/**
 * Safely read the Clerk user name without calling hooks that depend on
 * ClerkProvider being in the tree. Falls back to an empty string when
 * Clerk is not configured or the user has not signed in.
 */
function useClerkUserName(): { name: string; isLoaded: boolean } {
  const [result, setResult] = useState({ name: '', isLoaded: false })

  useEffect(() => {
    const clerkConfigured = !!process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY

    if (!clerkConfigured) {
      setResult({ name: '', isLoaded: true })
      return
    }

    // Clerk injects a global `window.Clerk` singleton. If it is already
    // loaded we can read the user immediately; otherwise we poll briefly.
    const existing = getClerkGlobal()
    if (existing?.loaded) {
      setResult({ name: formatClerkName(existing), isLoaded: true })
      return
    }

    const interval = setInterval(() => {
      const c = getClerkGlobal()
      if (c?.loaded) {
        clearInterval(interval)
        setResult({ name: formatClerkName(c), isLoaded: true })
      }
    }, 200)

    // Give up after 3 seconds so we never block onboarding.
    const timeout = setTimeout(() => {
      clearInterval(interval)
      setResult((prev) =>
        prev.isLoaded ? prev : { name: '', isLoaded: true }
      )
    }, 3000)

    return () => {
      clearInterval(interval)
      clearTimeout(timeout)
    }
  }, [])

  return result
}

/* -------------------------------------------------------------------------- */
/*  Page component                                                             */
/* -------------------------------------------------------------------------- */

/**
 * `/onboarding` -- Multi-step first-time user setup page.
 *
 * If the user has already completed onboarding (tracked via localStorage)
 * they are redirected straight to the dashboard. Otherwise the wizard is
 * rendered in a distraction-free layout (no header/footer).
 */
export default function OnboardingPage() {
  const router = useRouter()
  const { name: userName, isLoaded } = useClerkUserName()
  const [ready, setReady] = useState(false)

  useEffect(() => {
    if (!isLoaded) return

    if (hasCompletedOnboarding()) {
      router.replace('/')
      return
    }

    setReady(true)
  }, [isLoaded, router])

  if (!ready) {
    return (
      <RequireAuth>
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
      </RequireAuth>
    )
  }

  return (
    <RequireAuth>
      <main className="min-h-screen flex flex-col items-center justify-center px-4 py-12 sm:py-16">
        {/* Skip link for keyboard users */}
        <a
          href="#onboarding-wizard"
          className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:rounded-lg focus:bg-amber-600 focus:px-4 focus:py-2 focus:text-sm focus:font-medium focus:text-white"
        >
          Skip to onboarding wizard
        </a>

        <div id="onboarding-wizard" className="w-full">
          <OnboardingWizard initialName={userName} />
        </div>
      </main>
    </RequireAuth>
  )
}
