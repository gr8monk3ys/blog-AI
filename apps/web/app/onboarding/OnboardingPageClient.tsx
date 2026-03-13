'use client'

import { useEffect, useState } from 'react'
import OnboardingWizard from '../../components/onboarding/OnboardingWizard'

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
  const applyClerkResult = (name: string, isLoaded: boolean) => {
    setResult({ name, isLoaded })
  }

  useEffect(() => {
    const clerkConfigured = !!process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
    let resolved = false

    if (!clerkConfigured) {
      resolved = true
      applyClerkResult('', true)
      return
    }

    // Clerk injects a global `window.Clerk` singleton. If it is already
    // loaded we can read the user immediately; otherwise we poll briefly.
    const existing = getClerkGlobal()
    if (existing?.loaded) {
      resolved = true
      applyClerkResult(formatClerkName(existing), true)
      return
    }

    const interval = setInterval(() => {
      const c = getClerkGlobal()
      if (c?.loaded) {
        clearInterval(interval)
        resolved = true
        applyClerkResult(formatClerkName(c), true)
      }
    }, 200)

    // Give up after 3 seconds so we never block onboarding.
    const timeout = setTimeout(() => {
      clearInterval(interval)
      if (!resolved) {
        applyClerkResult('', true)
      }
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
 * Renders the onboarding wizard in a distraction-free layout (no header/footer).
 */
export default function OnboardingPageClient() {
  const { name: userName, isLoaded } = useClerkUserName()

  if (!isLoaded) {
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

  return (
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
  )
}
