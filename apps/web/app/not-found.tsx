'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'

const SUPPORT_EMAIL =
  process.env.NEXT_PUBLIC_SUPPORT_EMAIL || 'support@blogai.com'

/**
 * Custom 404 Not Found page
 *
 * This page is displayed when a user navigates to a route
 * that does not exist. It provides helpful navigation options
 * and maintains accessibility standards.
 */
export default function NotFound() {
  const router = useRouter()

  return (
    <main
      className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-950 dark:to-gray-900"
      role="main"
      aria-labelledby="not-found-title"
    >
      <div className="text-center px-4 py-16 max-w-lg">
        {/* Status Code */}
        <p
          className="text-8xl font-bold text-gray-200 dark:text-gray-800 select-none"
          aria-hidden="true"
        >
          404
        </p>

        {/* Title */}
        <h1
          id="not-found-title"
          className="mt-4 text-3xl font-bold tracking-tight text-gray-900 dark:text-gray-100 sm:text-4xl"
        >
          Page not found
        </h1>

        {/* Description */}
        <p className="mt-4 text-base leading-7 text-gray-600 dark:text-gray-400">
          Sorry, we could not find the page you are looking for. It may have
          been moved, deleted, or the URL might be incorrect.
        </p>

        {/* Navigation Options */}
        <nav className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link
            href="/"
            className="inline-flex items-center justify-center rounded-md bg-amber-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-amber-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-amber-600 transition-colors"
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
            Go back home
          </Link>

          <button
            type="button"
            onClick={() => router.back()}
            className="inline-flex items-center justify-center rounded-md bg-white dark:bg-gray-800 px-5 py-2.5 text-sm font-semibold text-gray-900 dark:text-gray-100 shadow-sm ring-1 ring-inset ring-gray-300 dark:ring-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-600 transition-colors"
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
                d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18"
              />
            </svg>
            Go back
          </button>
        </nav>

        {/* Help Text */}
        <p className="mt-10 text-sm text-gray-500 dark:text-gray-400">
          If you believe this is a mistake, please{' '}
          <a
            href={`mailto:${SUPPORT_EMAIL}`}
            className="text-amber-600 hover:text-amber-500 dark:text-amber-400 dark:hover:text-amber-300 underline underline-offset-2"
          >
            contact support
          </a>
          .
        </p>
      </div>
    </main>
  )
}
