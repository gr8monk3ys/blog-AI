/**
 * Route patterns that require an authenticated session.
 *
 * These are consumed by `proxy.ts` (the Next 16 name for `middleware.ts`) via
 * Clerk's `createRouteMatcher`, which matches each pattern against the request
 * pathname: RegExp entries are used directly with `RegExp.prototype.test`,
 * string entries are compiled with path-to-regexp.
 *
 * The list lives in its own module so it can be unit-tested without importing
 * `proxy.ts` (which pulls in `@clerk/nextjs/server` and the Next runtime).
 *
 * Rule of thumb when adding an entry: a prefix pattern such as `/foo(.*)`
 * swallows *every* route under `/foo`, including public marketing pages. Check
 * `app/sitemap.ts` before adding one.
 */
export const PROTECTED_ROUTE_PATTERNS: (string | RegExp)[] = [
  '/history(.*)',
  '/brand(.*)',
  '/admin(.*)',
  '/bulk(.*)',
  '/remix(.*)',
  '/analytics(.*)',
  // `/tools` (the browsable tool listing) and `/tools/category/[category]`
  // are PUBLIC marketing/SEO surfaces: they render SiteHeader/SiteFooter, fall
  // back to SAMPLE_TOOLS without any authenticated request, and are advertised
  // in `app/sitemap.ts`. Only the per-tool workspace at `/tools/[slug]` — which
  // generates content, writes history and reads brand profiles — needs a
  // session. A blanket `/tools(.*)` swallowed all three and 307'd the public
  // pages to the Clerk sign-in host.
  /^\/tools\/(?!category(?:\/|$))[^/]+/,
  '/templates(.*)',
  '/onboarding(.*)',
  '/plagiarism(.*)',
  '/images(.*)',
  '/settings(.*)',
  '/social(.*)',
  '/generate(.*)',
  '/knowledge(.*)',
  '/team(.*)',
]
