import { describe, it, expect } from 'vitest'
import { createPathMatcher } from '@clerk/shared/pathMatcher'
import { PROTECTED_ROUTE_PATTERNS } from '../../lib/protected-routes'

/**
 * `proxy.ts` feeds PROTECTED_ROUTE_PATTERNS to Clerk's `createRouteMatcher`,
 * which is a thin wrapper over `createPathMatcher(patterns)(req.nextUrl.pathname)`.
 * Matching the pathname through the same engine here means this test exercises
 * the real matching semantics, not a re-implementation of them.
 */
const isProtected = createPathMatcher(PROTECTED_ROUTE_PATTERNS)

describe('protected route matcher', () => {
  it.each([
    '/tools',
    '/tools/category/seo',
    '/tools/category/social-media',
    '/tools/category',
    '/tool-directory',
    '/',
    '/pricing',
    '/blog',
    '/blog/some-post',
    '/sign-in',
    '/sign-up',
  ])('leaves the public route %s unprotected', (pathname) => {
    expect(isProtected(pathname)).toBe(false)
  })

  it.each([
    '/admin',
    '/admin/blog',
    '/history',
    '/brand',
    '/brand/train',
    '/bulk',
    '/remix',
    '/analytics',
    '/templates',
    '/onboarding',
    '/plagiarism',
    '/images',
    '/settings/webhooks',
    '/social',
    '/generate',
    '/knowledge',
    '/team',
    // The per-tool workspace still requires a session.
    '/tools/blog-title-generator',
    '/tools/blog-title-generator/edit',
  ])('protects %s', (pathname) => {
    expect(isProtected(pathname)).toBe(true)
  })

  it('does not let a "category"-prefixed slug slip past the workspace gate', () => {
    // Only the real /tools/category/* subtree is public; a tool whose slug
    // merely starts with "category" must stay protected.
    expect(isProtected('/tools/categoryzer')).toBe(true)
  })
})
