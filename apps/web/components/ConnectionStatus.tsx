'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { ExclamationTriangleIcon, XMarkIcon } from '@heroicons/react/24/outline'
import { checkServerConnection } from '../lib/api'

const POLL_INTERVAL_MS = 30_000
const INITIAL_DELAY_MS = 2_000
// One failed probe is not an outage. The first check races page load, so a
// single abort there said "server down" while the API was answering normally.
const FAILURES_BEFORE_WARNING = 2

/**
 * Subtle banner that appears when the backend is unreachable.
 * Polls every 30 seconds and auto-hides once the connection is restored.
 *
 * A slip of paper card with a hairline, like the toast; only the icon carries
 * the warning colour (DESIGN.md → Colors → Signal). No shadow, no tinted fill.
 */
export default function ConnectionStatus(): React.ReactElement | null {
  const [status, setStatus] = useState<'connected' | 'disconnected' | 'checking'>('checking')
  const [dismissed, setDismissed] = useState(false)
  const consecutiveFailures = useRef(0)

  const check = useCallback(async () => {
    const ok = await checkServerConnection()

    if (ok) {
      consecutiveFailures.current = 0
      setStatus('connected')
      return
    }

    consecutiveFailures.current += 1
    if (consecutiveFailures.current < FAILURES_BEFORE_WARNING) return

    setStatus('disconnected')
    // Auto-show again if the connection drops after a dismissal
    setDismissed(false)
  }, [])

  useEffect(() => {
    // Delay the first check slightly so the page renders first
    const initialTimer = setTimeout(() => {
      void check()
    }, INITIAL_DELAY_MS)

    const interval = setInterval(() => {
      void check()
    }, POLL_INTERVAL_MS)

    return () => {
      clearTimeout(initialTimer)
      clearInterval(interval)
    }
  }, [check])

  // Nothing to show while checking or when connected
  if (status !== 'disconnected' || dismissed) return null

  return (
    <div
      role="status"
      aria-live="polite"
      className="fixed bottom-4 left-1/2 z-50 w-full max-w-md -translate-x-1/2 px-4"
    >
      <div className="flex items-center gap-3 rounded-lg border border-border bg-card px-4 py-3 text-sm text-card-foreground">
        <ExclamationTriangleIcon className="h-5 w-5 shrink-0 text-warning" aria-hidden="true" />
        <p className="flex-1">Unable to reach the server. Retrying automatically.</p>
        <button
          type="button"
          onClick={() => setDismissed(true)}
          className="shrink-0 rounded-full p-1 text-muted-foreground transition-colors hover:bg-muted hover:text-primary"
          aria-label="Dismiss connection warning"
        >
          <XMarkIcon className="h-4 w-4" aria-hidden="true" />
        </button>
      </div>
    </div>
  )
}
