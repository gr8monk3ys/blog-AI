/**
 * Routes that require an authenticated session.
 *
 * `proxy.ts` (the Next 16 name for `middleware.ts`) redirects requests for
 * these paths without a session cookie to /sign-in; each protected page then
 * validates the session itself (lib/auth-session.ts). The list lives in its
 * own module so it can be unit-tested without importing `proxy.ts`.
 *
 * Rule of thumb when adding an entry: a prefix pattern swallows *every* route
 * under it, including public marketing pages. Check `app/sitemap.ts` first.
 */
const prefix = (segment: string): RegExp => new RegExp(`^/${segment}(?:/|$)`)

export const PROTECTED_ROUTE_PATTERNS: RegExp[] = [
  prefix('history'),
  prefix('brand'),
  prefix('admin'),
  prefix('bulk'),
  prefix('remix'),
  prefix('analytics'),
  // `/tools` (the browsable tool listing) and `/tools/category/[category]`
  // are PUBLIC marketing/SEO surfaces: they render SiteHeader/SiteFooter, fall
  // back to SAMPLE_TOOLS without any authenticated request, and are advertised
  // in `app/sitemap.ts`. Only the per-tool workspace at `/tools/[slug]` — which
  // generates content, writes history and reads brand profiles — needs a
  // session.
  /^\/tools\/(?!category(?:\/|$))[^/]+/,
  prefix('templates'),
  prefix('onboarding'),
  prefix('plagiarism'),
  prefix('images'),
  prefix('settings'),
  prefix('social'),
  prefix('generate'),
  prefix('knowledge'),
  prefix('team'),
]

export function isProtectedPath(pathname: string): boolean {
  return PROTECTED_ROUTE_PATTERNS.some((pattern) => pattern.test(pathname))
}
