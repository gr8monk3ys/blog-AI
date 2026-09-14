/**
 * Sentry Client-Side Configuration
 *
 * This file configures Sentry for browser-side error tracking.
 * It runs in the browser and captures client-side errors, performance data,
 * and session replays.
 *
 * It is named `instrumentation-client.ts` because that is the file Next's
 * Turbopack build actually bundles; `sentry.client.config.ts` is silently
 * ignored there. Production served a server-side sentry-trace header but no
 * browser SDK until this rename.
 *
 * Session Replay is added *after* `Sentry.init`, from a dynamically imported
 * chunk scheduled on idle. Replay (rrweb) is ~60% of the SDK's browser bytes
 * and was the last unused/legacy-JS finding on the home page's mobile
 * Lighthouse run. Error capture and tracing are live from init; replay
 * attaches a moment later and still honours the sample rates set on init.
 */

import * as Sentry from '@sentry/nextjs'

// Lets the SDK instrument App Router navigations as transactions.
export const onRouterTransitionStart = Sentry.captureRouterTransitionStart

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
      /localhost/,
      /127\.0\.0\.1/,
      /.*\.vercel\.app/,
      /.*\.netlify\.app/,
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

  scheduleReplay()
}

/**
 * Loads Session Replay off the critical path.
 *
 * The dynamic import gives the bundler a split point so rrweb ships as its
 * own chunk instead of inside the SDK chunk every page loads eagerly. The
 * import is deferred to an idle callback (setTimeout fallback for Safari)
 * so it never competes with hydration. `addIntegration` on a live client
 * runs the integration's setup, so buffered/error-sampled replays work the
 * same as when the integration is passed to `init`.
 *
 * Privacy options are the same as before: mask all text, block all media.
 */
function scheduleReplay() {
  const load = () => {
    // `@sentry-internal/replay` is what `@sentry/nextjs` re-exports
    // `replayIntegration` from. Importing it directly (rather than
    // `import('@sentry/nextjs')`) keeps the lazy chunk to rrweb + replay
    // only; re-importing the whole SDK namespace made Turbopack emit a
    // 340 KB chunk that duplicated core code already in the initial bundle.
    void import('@sentry-internal/replay')
      .then(({ replayIntegration }) => {
        Sentry.addIntegration(
          replayIntegration({
            maskAllText: true,
            blockAllMedia: true,
          }),
        )
      })
      .catch(() => {
        // Replay is best-effort; error monitoring is already running.
      })
  }

  if (typeof window === 'undefined') return
  if ('requestIdleCallback' in window) {
    window.requestIdleCallback(load, { timeout: 5000 })
  } else {
    setTimeout(load, 1500)
  }
}
