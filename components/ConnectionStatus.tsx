'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { ExclamationTriangleIcon, XMarkIcon } from '@heroicons/react/24/outline'
import { checkServerConnection } from '../lib/api'

const POLL_INTERVAL_MS = 30_000
const INITIAL_DELAY_MS = 2_000

/**
 * Subtle banner that appears when the backend is unreachable.
 * Polls every 30 seconds and auto-hides once the connection is restored.
 */
export default function ConnectionStatus(): React.ReactElement | null {
  const [status, setStatus] = useState<'connected' | 'disconnected' | 'checking'>('checking')
  const [dismissed, setDismissed] = useState(false)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const check = useCallback(async () => {
    const ok = await checkServerConnection()
    setStatus(ok ? 'connected' : 'disconnected')
    // Auto-show again if the connection drops after a dismissal
    if (!ok) setDismissed(false)
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
      if (timerRef.current) clearTimeout(timerRef.current)
    }
  }, [check])

  // Nothing to show while checking or when connected
  if (status !== 'disconnected' || dismissed) return null

  return (
    <div
      role="status"
      aria-live="polite"
      className="fixed bottom-4 left-1/2 -translate-x-1/2 z-50 max-w-md w-full px-4"
    >
      <div className="flex items-center gap-3 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 shadow-lg text-sm">
        <ExclamationTriangleIcon className="h-5 w-5 flex-shrink-0 text-amber-500" aria-hidden="true" />
        <p className="flex-1 text-amber-800">
          Unable to reach the server. Retrying automatically.
        </p>
        <button
          type="button"
          onClick={() => setDismissed(true)}
          className="flex-shrink-0 rounded p-1 text-amber-600 hover:bg-amber-100 transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2"
          aria-label="Dismiss connection warning"
        >
          <XMarkIcon className="h-4 w-4" aria-hidden="true" />
        </button>
      </div>
    </div>
  )
}
