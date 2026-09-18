/**
 * Sentry Edge Runtime Configuration
 *
 * This file configures Sentry for Edge Runtime (middleware, edge functions).
 * Edge runtime has limited capabilities, so this config is minimal.
 */

import * as Sentry from '@sentry/nextjs'

import { SENTRY_DSN, SENTRY_ENABLED, SENTRY_ENVIRONMENT } from './lib/sentry-env'

// Only initialize Sentry when a DSN is configured AND this is a deployed
// Vercel app — same gate as the server and client runtimes.
if (SENTRY_ENABLED) {
  Sentry.init({
    dsn: SENTRY_DSN,

    // Lower trace rate for edge functions (they can be high volume)
    tracesSampleRate: process.env.NODE_ENV === 'production' ? 0.05 : 1.0,

    // Environment tagging: "production" or "preview", from VERCEL_ENV.
    environment: SENTRY_ENVIRONMENT,

    // Remove PII before sending
    beforeSend(event) {
      if (event.user) {
        delete event.user.ip_address
        delete event.user.email
      }
      return event
    },
  })
}
