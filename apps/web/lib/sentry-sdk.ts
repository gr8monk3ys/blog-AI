/**
 * The subset of `@sentry/nextjs` the browser actually calls.
 *
 * lib/sentry-client.ts loads this module with a dynamic `import()`. Pointing
 * that import at the SDK package directly would materialise its whole
 * namespace (every integration the SDK ships), because a dynamic import
 * cannot be tree-shaken; routing it through these named re-exports lets the
 * bundler drop everything else from the lazy chunk.
 */
export {
  init,
  addIntegration,
  captureException,
  captureRouterTransitionStart,
} from '@sentry/nextjs'
