import { describe, it, expect } from 'vitest'
import { isProtectedPath as isProtected } from '../../lib/protected-routes'

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
    '/forgot-password',
    '/reset-password',
    '/verify-email',
    '/api/auth/get-session',
    // A sibling that merely shares a prefix is not under the protected tree.
    '/historyx',
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
