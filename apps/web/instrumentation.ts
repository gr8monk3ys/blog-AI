/**
 * Next.js Instrumentation
 *
 * This file is loaded once when the Next.js server starts.
 * It's used to initialize Sentry on the server side.
 */

export async function register() {
  if (process.env.NEXT_RUNTIME === 'nodejs') {
    await import('./sentry.server.config')
  }

  if (process.env.NEXT_RUNTIME === 'edge') {
    await import('./sentry.edge.config')
  }
}
