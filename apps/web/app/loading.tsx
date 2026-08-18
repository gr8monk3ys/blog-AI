'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'

const HELP_TIMEOUT_MS = 8000

export default function Loading() {
  const [showHelp, setShowHelp] = useState(false)

  useEffect(() => {
    const timeout = window.setTimeout(() => setShowHelp(true), HELP_TIMEOUT_MS)
    return () => window.clearTimeout(timeout)
  }, [])

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100 dark:bg-gray-950 px-4">
      <div className="w-full max-w-md text-center">
        <div className="mx-auto mb-4 h-12 w-12 animate-spin rounded-full border-b-2 border-t-2 border-amber-600" />
        <p className="text-sm font-medium text-gray-700 dark:text-gray-300">Loading your workspace...</p>
        <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">This should only take a few seconds.</p>

        {showHelp ? (
          <div className="mt-6 rounded-lg border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-4 text-left">
            <p className="text-sm font-medium text-gray-900 dark:text-gray-100">Still loading?</p>
            <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
              Try a quick reload or jump to the tool directory while this page warms up.
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => window.location.reload()}
                className="inline-flex items-center rounded-md bg-amber-600 px-3 py-2 text-xs font-medium text-white hover:bg-amber-700"
              >
                Retry
              </button>
              <Link
                href="/tool-directory"
                className="inline-flex items-center rounded-md border border-gray-300 dark:border-gray-700 px-3 py-2 text-xs font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800"
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
