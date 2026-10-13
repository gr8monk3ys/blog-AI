import { describe, expect, it } from 'vitest'

import { buildAllowUrls } from '../../lib/sentry-client'

/**
 * Sentry drops any event whose frames match none of `allowUrls`. The list
 * used to name only localhost, *.vercel.app and *.netlify.app, so every error
 * raised on the live domain was discarded before it left the browser.
 */

const matches = (patterns: RegExp[], url: string) => patterns.some((pattern) => pattern.test(url))

describe('buildAllowUrls', () => {
  it('always allows the production domain', () => {
    const patterns = buildAllowUrls(null)

    expect(matches(patterns, 'https://blog-ai.vivancedata.com/_next/static/chunks/app.js')).toBe(true)
  })

  it('allows the configured site host as well', () => {
    const patterns = buildAllowUrls('staging.example.test')

    expect(matches(patterns, 'https://staging.example.test/_next/static/chunks/app.js')).toBe(true)
    expect(matches(patterns, 'https://blog-ai.vivancedata.com/x.js')).toBe(true)
  })

  it('escapes the host so dots are literal', () => {
    const patterns = buildAllowUrls('blog-ai.vivancedata.com')
    const hostPattern = patterns[patterns.length - 1]

    expect(hostPattern?.source).toBe('blog-ai\\.vivancedata\\.com')
    expect(matches([hostPattern as RegExp], 'https://blog-aixvivancedata.com/x.js')).toBe(false)
  })

  it('keeps the local and platform hosts', () => {
    const patterns = buildAllowUrls('localhost')

    expect(matches(patterns, 'http://localhost:3000/app.js')).toBe(true)
    expect(matches(patterns, 'http://127.0.0.1:3000/app.js')).toBe(true)
    expect(matches(patterns, 'https://blog-ai-abc.vercel.app/app.js')).toBe(true)
  })

  it('does not allow unrelated origins', () => {
    const patterns = buildAllowUrls('blog-ai.vivancedata.com')

    expect(matches(patterns, 'https://cdn.evil.example/inject.js')).toBe(false)
  })
})
