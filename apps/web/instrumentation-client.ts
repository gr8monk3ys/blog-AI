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
 * Nothing here imports `@sentry/nextjs` statically. The SDK (init options
 * live in lib/sentry-client.ts) is loaded on an idle callback after
 * hydration, so its ~100 KB gzip stays out of the chunk that gates
 * interactivity. Until it has loaded, window `error` and
 * `unhandledrejection` events are buffered and replayed into the SDK once
 * `init` has run, so early errors are still reported. Session Replay is
 * added after that, on a second idle callback, from its own chunk.
 */

import { getSentry, isSentryEnabled } from './lib/sentry-client'

// Lets the SDK instrument App Router navigations as transactions. Next calls
// this synchronously; the span is started as soon as the SDK is available,
// which is a microtask later once loaded.
export const onRouterTransitionStart = (
  ...args: Parameters<typeof import('./lib/sentry-sdk').captureRouterTransitionStart>
): void => {
  if (!isSentryEnabled()) return
  void getSentry().then((Sentry) => Sentry.captureRouterTransitionStart(...args)).catch(() => {})
}

type EarlyError = { kind: 'error'; event: ErrorEvent } | { kind: 'rejection'; event: PromiseRejectionEvent }

if (typeof window !== 'undefined' && isSentryEnabled()) {
  const early: EarlyError[] = []
  const onError = (event: ErrorEvent): void => {
    early.push({ kind: 'error', event })
  }
  const onRejection = (event: PromiseRejectionEvent): void => {
    early.push({ kind: 'rejection', event })
  }
  window.addEventListener('error', onError)
  window.addEventListener('unhandledrejection', onRejection)

  const load = (): void => {
    void getSentry()
      .then((Sentry) => {
        window.removeEventListener('error', onError)
        window.removeEventListener('unhandledrejection', onRejection)
        for (const item of early.splice(0)) {
          const value = item.kind === 'error' ? (item.event.error ?? item.event.message) : item.event.reason
          Sentry.captureException(value, {
            mechanism: { type: item.kind === 'error' ? 'onerror' : 'onunhandledrejection', handled: false },
          })
        }
        onIdle(() => scheduleReplay(Sentry))
      })
      .catch(() => {
        // Monitoring is best-effort; never let it break the page.
      })
  }

  onIdle(load)
}

function onIdle(fn: () => void): void {
  if ('requestIdleCallback' in window) {
    window.requestIdleCallback(fn, { timeout: 3000 })
  } else {
    setTimeout(fn, 1500)
  }
}

/**
 * Loads Session Replay off the critical path (see lib/sentry-replay.ts for
 * why it is imported that way). `addIntegration` on a live client runs the
 * integration's setup, so buffered/error-sampled replays work the same as
 * when the integration is passed to `init`.
 *
 * Privacy options are the same as before: mask all text, block all media.
 */
function scheduleReplay(Sentry: Awaited<ReturnType<typeof getSentry>>): void {
  void import('./lib/sentry-replay')
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
