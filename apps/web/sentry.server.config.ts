/**
 * Sentry Server-Side Configuration
 *
 * This file configures Sentry for server-side error tracking in Next.js.
 * It runs in Node.js and captures API route errors, server component errors,
 * and server-side rendering issues.
 */

import * as Sentry from '@sentry/nextjs'

import { SENTRY_DSN, SENTRY_ENABLED, SENTRY_ENVIRONMENT } from './lib/sentry-env'

// Only initialize Sentry when a DSN is configured AND this is a deployed
// Vercel app. A local `next build && next start` has NODE_ENV=production but
// no VERCEL_ENV, and used to report into the org's shared error quota.
if (SENTRY_ENABLED) {
  Sentry.init({
    dsn: SENTRY_DSN,

    // Performance Monitoring
    tracesSampleRate: process.env.NODE_ENV === 'production' ? 0.1 : 1.0,

    // Environment tagging: "production" or "preview", from VERCEL_ENV.
    environment: SENTRY_ENVIRONMENT,

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
