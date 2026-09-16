/**
 * Session Replay, imported lazily from instrumentation-client.ts.
 *
 * `@sentry-internal/replay` is what `@sentry/nextjs` re-exports
 * `replayIntegration` from; importing it directly (rather than the SDK
 * namespace) keeps the lazy chunk to rrweb + replay only. Named re-export
 * for the same tree-shaking reason as lib/sentry-sdk.ts.
 */
export { replayIntegration } from '@sentry-internal/replay'
