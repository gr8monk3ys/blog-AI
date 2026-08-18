'use client'

import * as Sentry from '@sentry/nextjs'
import { useEffect } from 'react'
import Link from 'next/link'

const SUPPORT_EMAIL =
  process.env.NEXT_PUBLIC_SUPPORT_EMAIL || 'support@blogai.com'

/**
 * Error Boundary Component
 *
 * This component handles errors that occur within the app layout.
 * It provides a user-friendly error message and recovery options,
 * while also reporting errors to Sentry for monitoring.
 *
 * Accessibility features:
 * - Proper heading hierarchy
 * - ARIA labels for interactive elements
 * - Focus management for keyboard users
 * - Screen reader announcements
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
    Sentry.captureException(error, {
      tags: {
        errorBoundary: 'app',
      },
      extra: {
        digest: error.digest,
      },
    })
  }, [error])

  return (
    <main
      className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-950 dark:to-gray-900 px-4"
      role="main"
      aria-labelledby="error-title"
    >
      <div className="bg-white dark:bg-gray-900 p-8 rounded-xl shadow-lg text-center max-w-lg w-full">
        {/* Error Icon */}
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-red-100 dark:bg-red-900/30 mb-6">
          <svg
            className="h-8 w-8 text-red-600 dark:text-red-400"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={1.5}
            stroke="currentColor"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z"
            />
          </svg>
        </div>

        {/* Title */}
        <h1
          id="error-title"
          className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-3"
        >
          Something went wrong
        </h1>

        {/* Description */}
        <p className="text-gray-600 dark:text-gray-400 mb-6 leading-relaxed">
          We encountered an unexpected error while processing your request.
          Our team has been notified and is working to resolve the issue.
        </p>

        {/* Error ID for support reference */}
        {error.digest && (
          <div
            className="bg-gray-50 dark:bg-gray-800/50 rounded-lg px-4 py-3 mb-6 text-sm text-gray-500 dark:text-gray-400 font-mono"
            aria-label="Error reference ID"
          >
            Error ID: {error.digest}
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <button
            onClick={() => reset()}
            className="inline-flex items-center justify-center px-5 py-2.5 rounded-lg bg-amber-600 text-white font-semibold shadow-sm hover:bg-amber-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-amber-600 transition-colors"
            type="button"
          >
            <svg
              className="mr-2 h-4 w-4"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={2}
              stroke="currentColor"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99"
              />
            </svg>
            Try again
          </button>

          <Link
            href="/"
            className="inline-flex items-center justify-center px-5 py-2.5 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 font-semibold shadow-sm ring-1 ring-inset ring-gray-300 dark:ring-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-600 transition-colors"
          >
            <svg
              className="mr-2 h-4 w-4"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={2}
              stroke="currentColor"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M2.25 12l8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25"
              />
            </svg>
            Return home
          </Link>
        </div>

        {/* Help Text */}
        <p className="mt-8 text-sm text-gray-500 dark:text-gray-400">
          Need help?{' '}
          <a
            href={`mailto:${SUPPORT_EMAIL}`}
            className="text-amber-600 hover:text-amber-500 dark:text-amber-400 dark:hover:text-amber-300 underline underline-offset-2"
          >
            Contact support
          </a>
        </p>
      </div>
    </main>
  )
}
