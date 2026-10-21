/**
 * The one place the web app decides what its own public origin is.
 *
 * Used by the sitemap, the RSS feed, Sentry's `allowUrls` and (after the pages
 * PR) `metadataBase` in app/layout.tsx. Until then layout.tsx still carries its
 * own `https://blogai.com` fallback -- a domain this project does not own.
 *
 * Resolution order:
 *   1. NEXT_PUBLIC_SITE_URL      -- explicit; set it in every Vercel environment.
 *   2. Vercel production build   -- the real domain. VERCEL_URL would give the
 *                                   per-deployment *.vercel.app host, which is
 *                                   the wrong canonical for a sitemap.
 *   3. Any other Vercel build    -- https://$VERCEL_URL (preview deployments).
 *   4. Otherwise                 -- http://localhost:3000.
 */

/** The domain production serves from (verified live 2026-10-13). */
export const PRODUCTION_SITE_URL = 'https://blog-ai.vivancedata.com'

const stripTrailingSlash = (url: string): string => url.replace(/\/$/, '')

const getBaseUrl = (): string => {
  const explicit = process.env.NEXT_PUBLIC_SITE_URL?.trim()
  if (explicit) {
    return stripTrailingSlash(explicit)
  }

  const vercelEnv = process.env.NEXT_PUBLIC_VERCEL_ENV || process.env.VERCEL_ENV
  if (vercelEnv === 'production') {
    return PRODUCTION_SITE_URL
  }

  if (process.env.VERCEL_URL) {
    return stripTrailingSlash(`https://${process.env.VERCEL_URL}`)
  }

  return 'http://localhost:3000'
}

/**
 * Host name of `getBaseUrl()` (no scheme, no port), or null when the value is
 * not a parseable URL. Sentry's `allowUrls` wants the host, not the origin.
 */
export const getSiteHost = (): string | null => {
  try {
    return new URL(getBaseUrl()).hostname || null
  } catch {
    return null
  }
}

export { getBaseUrl }
export default getBaseUrl
