'use client'

import OnboardingWizard from '../../components/onboarding/OnboardingWizard'
import { authClient } from '../../lib/auth-client'

/* -------------------------------------------------------------------------- */
/*  Page component                                                             */
/* -------------------------------------------------------------------------- */

/**
 * `/onboarding` -- Multi-step first-time user setup page.
 *
 * Renders the onboarding wizard in a distraction-free layout (no header/footer).
 */
export default function OnboardingPageClient() {
  const { data: session, isPending } = authClient.useSession()
  const userName = session?.user.name ?? ''

  if (isPending) {
    return (
      <main id="main-content" tabIndex={-1} className="min-h-screen flex items-center justify-center">
        <div className="flex items-center gap-3" role="status" aria-label="Loading">
          <div className="h-2.5 w-2.5 rounded-full bg-amber-400 animate-pulse" />
          <div
            className="h-2.5 w-2.5 rounded-full bg-amber-500 animate-pulse"
            style={{ animationDelay: '150ms' }}
          />
          <div
            className="h-2.5 w-2.5 rounded-full bg-amber-600 animate-pulse"
            style={{ animationDelay: '300ms' }}
          />
        </div>
      </main>
    )
  }

  return (
    <main id="main-content" tabIndex={-1} className="min-h-screen flex flex-col items-center justify-center px-4 py-12 sm:py-16">
      {/* Skip link for keyboard users */}
      <a
        href="#onboarding-wizard"
        className="sr-only focus-visible:not-sr-only focus-visible:absolute focus-visible:top-4 focus-visible:left-4 focus-visible:z-50 focus-visible:rounded-lg focus-visible:bg-amber-700 focus-visible:px-4 focus-visible:py-2 focus-visible:text-sm focus-visible:font-medium focus-visible:text-white"
      >
        Skip to onboarding wizard
      </a>

      <div id="onboarding-wizard" className="w-full">
        <OnboardingWizard initialName={userName} />
      </div>
    </main>
  )
}
