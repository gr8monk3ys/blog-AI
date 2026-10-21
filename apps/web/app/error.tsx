'use client'

import { useEffect } from 'react'
import Link from 'next/link'
import { getSentry } from '../lib/sentry-client'
import { Button } from '../components/ui/Button'

const SUPPORT_EMAIL = process.env.NEXT_PUBLIC_SUPPORT_EMAIL ?? 'support@lscaturchio.xyz'

/**
 * Error Boundary Component
 *
 * Handles errors that occur within the app layout and reports them to Sentry.
 * The page is an honest error state in the house voice (DESIGN.md → Do): a
 * wall label, one serif line, one primary action, the error reference as a
 * mono label for support.
 */
export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  // Report error to Sentry on mount
  useEffect(() => {
    void getSentry()
      .then((Sentry) => {
        Sentry.captureException(error, {
          tags: {
            errorBoundary: 'app',
          },
          extra: {
            digest: error.digest,
          },
        })
      })
      .catch(() => {
        // Reporting is best-effort; the error UI is already shown.
      })
  }, [error])

  return (
    <main
      id="main-content"
      tabIndex={-1}
      className="flex min-h-screen flex-col justify-center"
      role="main"
      aria-labelledby="error-title"
    >
      <div className="mx-auto w-full max-w-2xl px-4 py-16 sm:px-6 md:py-24 lg:px-8">
        <p className="label-mono">Error</p>

        <h1 id="error-title" className="text-page-title mt-4">
          Something Went Wrong
        </h1>

        <p className="mt-4 max-w-xl text-lg leading-relaxed text-muted-foreground text-pretty">
          We encountered an unexpected error while processing your request. Our team has been
          notified and is working to resolve the issue.
        </p>

        {error.digest && (
          <p className="label-mono mt-6 normal-case tracking-normal" aria-label="Error reference ID">
            Error ID: {error.digest}
          </p>
        )}

        <div className="mt-8 flex flex-wrap items-center gap-5">
          <Button type="button" size="lg" onClick={() => reset()}>
            Try Again
          </Button>
          <Link
            href="/"
            className="label-mono label-link ink-underline transition-colors hover:text-primary"
          >
            Return Home
          </Link>
        </div>

        <p className="mt-12 border-t border-border pt-6 text-sm text-muted-foreground">
          Need help?{' '}
          <a href={`mailto:${SUPPORT_EMAIL}`} className="ink-underline text-primary">
            Contact Support
          </a>
        </p>
      </div>
    </main>
  )
}
