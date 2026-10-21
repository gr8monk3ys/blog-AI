'use client'

import { useEffect } from 'react'
import { getSentry } from '../lib/sentry-client'
import Link from 'next/link'

/**
 * Global Error Boundary
 *
 * Handles errors that occur outside of the normal app layout, including
 * errors in the root layout itself. It renders a completely self-contained
 * document without relying on any shared layout or stylesheet, so the
 * notebook's stationery is written out here by hand: paper and Iron Gall
 * (DESIGN.md → Colors), the body sans and a mono label from the system
 * stacks, flat surfaces, one primary action.
 *
 * Note: This component must define its own <html> and <body> tags as it
 * replaces the entire document when triggered.
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
    void getSentry()
      .then((Sentry) => {
        Sentry.captureException(error, {
          tags: {
            errorBoundary: 'global',
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

  // Inline styles: Tailwind and globals.css are not available in global error.
  // Paper #f9f8f5, Ink #1a1f23, Ink Muted #606976, Hairline #e2dbd5, Iron
  // Gall #2a3f79 — the light tokens from DESIGN.md.
  const styles = {
    body: {
      margin: 0,
      padding: '1rem',
      fontFamily: "'Instrument Sans', ui-sans-serif, system-ui, sans-serif",
      background: '#f9f8f5',
      color: '#1a1f23',
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      lineHeight: 1.65,
    } as const,
    container: {
      maxWidth: '42rem',
      width: '100%',
    },
    label: {
      margin: 0,
      fontFamily: "'IBM Plex Mono', ui-monospace, SFMono-Regular, Menlo, monospace",
      fontSize: '0.72rem',
      fontWeight: 500,
      letterSpacing: '0.16em',
      textTransform: 'uppercase' as const,
      color: '#606976',
    },
    title: {
      fontFamily: "Fraunces, ui-serif, Georgia, serif",
      fontSize: 'clamp(1.9rem, 3.6vw, 3.2rem)',
      fontWeight: 700,
      lineHeight: 1.12,
      letterSpacing: '-0.03em',
      marginTop: '1rem',
      marginBottom: 0,
    },
    message: {
      color: '#606976',
      fontSize: '1.125rem',
      lineHeight: 1.65,
      marginTop: '1rem',
      marginBottom: 0,
      maxWidth: '36rem',
    },
    errorId: {
      fontFamily: "'IBM Plex Mono', ui-monospace, SFMono-Regular, Menlo, monospace",
      fontSize: '0.8rem',
      color: '#606976',
      marginTop: '1.5rem',
      wordBreak: 'break-all' as const,
    },
    actions: {
      display: 'flex',
      flexWrap: 'wrap' as const,
      alignItems: 'center',
      gap: '1.25rem',
      marginTop: '2rem',
    },
    btnPrimary: {
      display: 'inline-flex',
      alignItems: 'center',
      justifyContent: 'center',
      height: '3rem',
      padding: '0 2rem',
      borderRadius: '0.875rem',
      fontSize: '1rem',
      fontWeight: 500,
      fontFamily: 'inherit',
      cursor: 'pointer',
      background: '#2a3f79',
      color: '#ffffff',
      border: '1px solid rgba(42, 63, 121, 0.42)',
      boxShadow: '0 1px 0 rgba(42, 63, 121, 0.25)',
    },
    link: {
      fontFamily: "'IBM Plex Mono', ui-monospace, SFMono-Regular, Menlo, monospace",
      fontSize: '0.72rem',
      fontWeight: 500,
      letterSpacing: '0.16em',
      textTransform: 'uppercase' as const,
      color: '#2a3f79',
      textDecoration: 'underline',
      textUnderlineOffset: '4px',
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
          <p style={styles.label}>Error</p>

          <h1 id="error-title" style={styles.title}>
            Something Went Wrong
          </h1>

          <p style={styles.message}>
            We encountered an unexpected error. Our team has been notified and
            is working to fix the issue. Please try again or return to the home
            page.
          </p>

          {error.digest && (
            <p style={styles.errorId} aria-label="Error reference ID">
              Error ID: {error.digest}
            </p>
          )}

          <div style={styles.actions}>
            <button onClick={() => reset()} style={styles.btnPrimary} type="button">
              Try Again
            </button>
            <Link href="/" style={styles.link}>
              Return Home
            </Link>
          </div>
        </main>
      </body>
    </html>
  )
}
