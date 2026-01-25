'use client'

import * as Sentry from '@sentry/nextjs'
import { useEffect } from 'react'

/**
 * Global Error Boundary
 *
 * This component handles errors that occur outside of the normal
 * app layout, including errors in the root layout itself. It
 * renders a completely self-contained error page without relying
 * on any shared layout or styles.
 *
 * Note: This component must define its own <html> and <body> tags
 * as it replaces the entire document when triggered.
 */
export default function GlobalError({
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
        errorBoundary: 'global',
      },
      extra: {
        digest: error.digest,
      },
    })
  }, [error])

  // Inline styles since Tailwind is not available in global error
  const styles = {
    body: {
      margin: 0,
      padding: '1rem',
      fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif",
      background: 'linear-gradient(135deg, #f5f7fa 0%, #e4e8ed 100%)',
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
    } as const,
    container: {
      background: 'white',
      borderRadius: '12px',
      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1)',
      padding: '2.5rem',
      maxWidth: '480px',
      width: '100%',
      textAlign: 'center' as const,
    },
    icon: {
      width: '64px',
      height: '64px',
      margin: '0 auto 1.5rem',
      color: '#dc2626',
    },
    title: {
      color: '#111827',
      fontSize: '1.5rem',
      fontWeight: 700,
      marginBottom: '0.75rem',
      marginTop: 0,
    },
    message: {
      color: '#4b5563',
      fontSize: '1rem',
      lineHeight: 1.625,
      marginBottom: '1.5rem',
    },
    errorId: {
      background: '#f3f4f6',
      borderRadius: '6px',
      padding: '0.75rem 1rem',
      fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace',
      fontSize: '0.875rem',
      color: '#6b7280',
      marginBottom: '1.5rem',
      wordBreak: 'break-all' as const,
    },
    buttons: {
      display: 'flex',
      flexDirection: 'column' as const,
      gap: '0.75rem',
      justifyContent: 'center',
    },
    btnPrimary: {
      display: 'inline-flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '0.625rem 1.25rem',
      borderRadius: '6px',
      fontSize: '0.875rem',
      fontWeight: 600,
      textDecoration: 'none',
      cursor: 'pointer',
      transition: 'all 0.15s ease',
      background: '#2563eb',
      color: 'white',
      border: 'none',
    },
    btnSecondary: {
      display: 'inline-flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '0.625rem 1.25rem',
      borderRadius: '6px',
      fontSize: '0.875rem',
      fontWeight: 600,
      textDecoration: 'none',
      cursor: 'pointer',
      transition: 'all 0.15s ease',
      background: 'white',
      color: '#374151',
      border: '1px solid #d1d5db',
    },
  }

  return (
    <html lang="en">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Application Error - Blog AI</title>
      </head>
      <body style={styles.body}>
        <main style={styles.container} role="main" aria-labelledby="error-title">
          {/* Error Icon */}
          <svg
            style={styles.icon}
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={1.5}
            stroke="currentColor"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"
            />
          </svg>

          {/* Title */}
          <h1 id="error-title" style={styles.title}>
            Something went wrong
          </h1>

          {/* Message */}
          <p style={styles.message}>
            We encountered an unexpected error. Our team has been notified and
            is working to fix the issue. Please try again or return to the home
            page.
          </p>

          {/* Error ID for support reference */}
          {error.digest && (
            <div style={styles.errorId} aria-label="Error reference ID">
              Error ID: {error.digest}
            </div>
          )}

          {/* Action Buttons */}
          <div style={styles.buttons}>
            <button
              onClick={() => reset()}
              style={styles.btnPrimary}
              type="button"
            >
              Try again
            </button>
            <a href="/" style={styles.btnSecondary}>
              Return home
            </a>
          </div>
        </main>
      </body>
    </html>
  )
}
