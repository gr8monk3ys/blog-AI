'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { buttonVariants } from '../components/ui/Button'

const HELP_TIMEOUT_MS = 8000

// The route loading state: a spinner in the ink, one line of body copy, and
// after eight seconds an honest "still loading" note with one primary action.
// `animate-spin` is one of the two loading indicators that slow rather than
// stop under prefers-reduced-motion (DESIGN.md → Motion).
export default function Loading() {
  const [showHelp, setShowHelp] = useState(false)

  useEffect(() => {
    const timeout = window.setTimeout(() => setShowHelp(true), HELP_TIMEOUT_MS)
    return () => window.clearTimeout(timeout)
  }, [])

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div
          className="size-10 animate-spin rounded-full border-2 border-border border-t-primary"
          aria-hidden="true"
        />
        <p className="label-mono mt-6" role="status">
          Loading your workspace…
        </p>
        <p className="mt-2 text-sm text-muted-foreground">This should only take a few seconds.</p>

        {showHelp ? (
          <div className="mt-8 border-t border-border pt-6">
            <h2 className="text-card-title">Still loading?</h2>
            <p className="mt-2 text-sm text-muted-foreground">
              Try a quick reload or jump to the tool directory while this page warms up.
            </p>
            <div className="mt-5 flex flex-wrap items-center gap-5">
              <button
                type="button"
                onClick={() => window.location.reload()}
                className={buttonVariants()}
              >
                Retry
              </button>
              <Link
                href="/tool-directory"
                className="label-mono label-link ink-underline transition-colors hover:text-primary"
              >
                Open Tool Directory
              </Link>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  )
}
