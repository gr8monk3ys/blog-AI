/**
 * The deployed-environment gate shared by every Sentry entry point in the web
 * app (instrumentation-client.ts via lib/sentry-client.ts, sentry.server.config.ts,
 * sentry.edge.config.ts).
 *
 * Why it exists: the `vivance` Sentry org shares ONE error quota across all of
 * its projects, and 36% of the error events it accepted in the 30 days to
 * 2026-09-13 were tagged `environment:development` — this app running on a
 * laptop (`http://127.0.0.1:...`), reporting into the production quota until
 * that quota was exhausted org-wide and every project stopped receiving
 * errors. Per-DSN rate limits are not available on the plan, so this
 * build-time gate is the only control there is.
 *
 * How it decides: Vercel sets VERCEL_ENV to "production" | "preview" |
 * "development", and only sets it in a deployed build. It is undefined for
 * `next dev` AND for a local `next build && next start` — which is exactly the
 * case that burned the quota, and exactly the case NODE_ENV cannot catch,
 * since a local production build sets NODE_ENV=production too.
 *
 * The browser bundle can only read NEXT_PUBLIC_* variables (plain VERCEL_ENV
 * is erased from it), so next.config.mjs mirrors VERCEL_ENV into
 * NEXT_PUBLIC_VERCEL_ENV at build time. Server and edge read either one.
 *
 * Escape hatches — both are build-time values, so they must be set for the
 * `build`, not just for `start`:
 *
 *   NEXT_PUBLIC_SENTRY_FORCE_ENABLE=1 bun run build && bun run start
 *     turns reporting ON off-Vercel, for deliberately exercising the SDK
 *     wiring locally. Point NEXT_PUBLIC_SENTRY_DSN at a throwaway project
 *     first — the shared quota is the thing being protected.
 *
 *   NEXT_PUBLIC_SENTRY_FORCE_DISABLE=1
 *     turns reporting OFF even in a deployed build: a kill switch for a
 *     deploy that is flooding the shared quota. Set it in Vercel and redeploy.
 */

const SENTRY_DSN = process.env.NEXT_PUBLIC_SENTRY_DSN

/** "production" | "preview" | "development" on Vercel; undefined anywhere else. */
const VERCEL_ENV = process.env.NEXT_PUBLIC_VERCEL_ENV || process.env.VERCEL_ENV

const FORCE_ENABLE = process.env.NEXT_PUBLIC_SENTRY_FORCE_ENABLE === '1'
const FORCE_DISABLE = process.env.NEXT_PUBLIC_SENTRY_FORCE_DISABLE === '1'

/** A real Vercel deployment. "development" is Vercel's value for `vercel dev`. */
const IS_DEPLOYED = VERCEL_ENV === 'production' || VERCEL_ENV === 'preview'

/**
 * The `environment` tag on every event: the resolved Vercel value, so
 * production and preview stay distinguishable in Sentry.
 *
 * Off Vercel it is "local", never NODE_ENV — a local production build has
 * NODE_ENV=production, and tagging those events "production" is how a leak
 * hides. Only a forced local run (see above) can ever emit this tag, and when
 * one does it is obvious in Sentry which is exactly what is wanted.
 */
export const SENTRY_ENVIRONMENT: string = VERCEL_ENV || 'local'

/** True only when this build may initialise Sentry and report events. */
export const SENTRY_ENABLED: boolean =
  Boolean(SENTRY_DSN) && (IS_DEPLOYED || FORCE_ENABLE) && !FORCE_DISABLE

export { SENTRY_DSN }
