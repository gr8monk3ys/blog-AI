/**
 * Lazy browser Sentry.
 *
 * The SDK used to be imported statically from instrumentation-client.ts and
 * the three error boundaries, which put ~100 KB (gzip) of Sentry into the
 * chunk every page must evaluate before it is interactive. On the mobile
 * Lighthouse run of the home page that chunk was the single largest script
 * and the largest slice of Total Blocking Time.
 *
 * `getSentry()` is the only way client code reaches the SDK now. It loads
 * the module on demand, runs `Sentry.init` exactly once, and resolves to the
 * initialised module, so callers can never capture into an un-initialised
 * client (which silently drops the event). instrumentation-client.ts warms
 * it on an idle callback; an error boundary that fires first simply triggers
 * the load itself and reports once init has run.
 */

type SentryModule = typeof import('./sentry-sdk')

const SENTRY_DSN = process.env.NEXT_PUBLIC_SENTRY_DSN

let sentryPromise: Promise<SentryModule> | null = null

function init(Sentry: SentryModule): SentryModule {
  if (!SENTRY_DSN) return Sentry

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

  return Sentry
}

/**
 * Resolves to the Sentry module with `init` already applied (once).
 *
 * The import goes through lib/sentry-sdk.ts (named re-exports) rather than
 * `@sentry/nextjs` itself: a dynamic import of the package would keep its
 * whole namespace alive and the lazy chunk grew by ~60 KB gzip that way.
 */
export function getSentry(): Promise<SentryModule> {
  if (!sentryPromise) {
    sentryPromise = import('./sentry-sdk').then(init)
  }
  return sentryPromise
}

/** True when a DSN is configured, i.e. `getSentry()` will actually report. */
export function isSentryEnabled(): boolean {
  return !!SENTRY_DSN
}
