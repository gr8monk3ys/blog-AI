/**
 * Sentry Server-Side Configuration
 *
 * This file configures Sentry for server-side error tracking in Next.js.
 * It runs in Node.js and captures API route errors, server component errors,
 * and server-side rendering issues.
 */

import * as Sentry from '@sentry/nextjs'

const SENTRY_DSN = process.env.NEXT_PUBLIC_SENTRY_DSN

// Only initialize Sentry if DSN is configured
if (SENTRY_DSN) {
  Sentry.init({
    dsn: SENTRY_DSN,

    // Performance Monitoring
    tracesSampleRate: process.env.NODE_ENV === 'production' ? 0.1 : 1.0,

    // Environment tagging
    environment: process.env.NODE_ENV,

    // Filter out common server-side noise
    ignoreErrors: [
      // Connection errors (often transient)
      'ECONNREFUSED',
      'ECONNRESET',
      'ETIMEDOUT',
      // Rate limiting (expected behavior)
      'Too Many Requests',
      '429',
      // Cancelled requests
      'AbortError',
      'The operation was aborted',
    ],

    // Remove PII before sending
    beforeSend(event) {
      // Remove user IP addresses
      if (event.user) {
        delete event.user.ip_address
        delete event.user.email
      }

      // Remove cookies and headers that might contain sensitive data
      if (event.request) {
        delete event.request.cookies
        if (event.request.headers) {
          delete event.request.headers['authorization']
          delete event.request.headers['x-api-key']
          delete event.request.headers['cookie']
        }
      }

      return event
    },

    // Debug mode for development
    debug: process.env.NODE_ENV === 'development',
  })
}
