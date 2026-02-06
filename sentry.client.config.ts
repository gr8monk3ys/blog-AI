/**
 * Sentry Client-Side Configuration
 *
 * This file configures Sentry for browser-side error tracking.
 * It runs in the browser and captures client-side errors, performance data,
 * and session replays.
 */

import * as Sentry from '@sentry/nextjs'

const SENTRY_DSN = process.env.NEXT_PUBLIC_SENTRY_DSN

// Only initialize Sentry if DSN is configured
if (SENTRY_DSN) {
  Sentry.init({
    dsn: SENTRY_DSN,

    // Performance Monitoring
    tracesSampleRate: process.env.NODE_ENV === 'production' ? 0.1 : 1.0,

    // Session Replay - captures user sessions for debugging
    replaysSessionSampleRate: 0.1, // 10% of sessions
    replaysOnErrorSampleRate: 1.0, // 100% of sessions with errors

    // Environment tagging
    environment: process.env.NODE_ENV,

    // Privacy: Mask all text and block media to protect user data
    integrations: [
      Sentry.replayIntegration({
        maskAllText: true,
        blockAllMedia: true,
      }),
    ],

    // Filter out common noise
    ignoreErrors: [
      // Browser extensions
      /extensions\//i,
      /^chrome:\/\//i,
      /^moz-extension:\/\//i,
      // Network errors
      'Network Error',
      'NetworkError',
      'Failed to fetch',
      'Load failed',
      // Hydration warnings (common in Next.js)
      'Hydration failed',
      'Text content does not match',
      // User-initiated cancellations
      'AbortError',
      'The operation was aborted',
    ],

    // Only capture errors from our domain
    allowUrls: [
      // Add your production domain here
      /localhost/,
      /127\.0\.0\.1/,
    ],

    // Remove PII before sending
    beforeSend(event) {
      // Remove user IP addresses
      if (event.user) {
        delete event.user.ip_address
        delete event.user.email
      }

      // Remove cookies from request data
      if (event.request?.cookies) {
        delete event.request.cookies
      }

      return event
    },

    // Debug mode for development
    debug: process.env.NODE_ENV === 'development',
  })
}
