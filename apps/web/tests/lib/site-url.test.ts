import { afterEach, describe, expect, it, vi } from 'vitest'

import getBaseUrl, { PRODUCTION_SITE_URL, getSiteHost } from '../../lib/site-url'

const ENV_KEYS = ['NEXT_PUBLIC_SITE_URL', 'NEXT_PUBLIC_VERCEL_ENV', 'VERCEL_ENV', 'VERCEL_URL'] as const

afterEach(() => {
  vi.unstubAllEnvs()
})

function clearEnv() {
  for (const key of ENV_KEYS) vi.stubEnv(key, '')
}

describe('getBaseUrl', () => {
  it('prefers NEXT_PUBLIC_SITE_URL and strips a trailing slash', () => {
    clearEnv()
    vi.stubEnv('NEXT_PUBLIC_SITE_URL', 'https://example.test/')
    vi.stubEnv('VERCEL_ENV', 'production')

    expect(getBaseUrl()).toBe('https://example.test')
  })

  it('uses the real production domain on a Vercel production build, not VERCEL_URL', () => {
    clearEnv()
    vi.stubEnv('VERCEL_ENV', 'production')
    vi.stubEnv('VERCEL_URL', 'blog-ai-abc123-gr8monk3ys-projects.vercel.app')

    expect(getBaseUrl()).toBe(PRODUCTION_SITE_URL)
    expect(PRODUCTION_SITE_URL).toBe('https://blog-ai.vivancedata.com')
  })

  it('honours the NEXT_PUBLIC_VERCEL_ENV mirror the client bundle sees', () => {
    clearEnv()
    vi.stubEnv('NEXT_PUBLIC_VERCEL_ENV', 'production')

    expect(getBaseUrl()).toBe(PRODUCTION_SITE_URL)
  })

  it('uses https://$VERCEL_URL for preview deployments', () => {
    clearEnv()
    vi.stubEnv('VERCEL_ENV', 'preview')
    vi.stubEnv('VERCEL_URL', 'blog-ai-git-feature-gr8monk3ys-projects.vercel.app')

    expect(getBaseUrl()).toBe('https://blog-ai-git-feature-gr8monk3ys-projects.vercel.app')
  })

  it('falls back to localhost off Vercel', () => {
    clearEnv()

    expect(getBaseUrl()).toBe('http://localhost:3000')
  })
})

describe('getSiteHost', () => {
  it('returns the bare host name', () => {
    clearEnv()
    vi.stubEnv('NEXT_PUBLIC_SITE_URL', 'https://staging.example.test:8443/base')

    expect(getSiteHost()).toBe('staging.example.test')
  })

  it('returns null when the configured value is not a URL', () => {
    clearEnv()
    vi.stubEnv('NEXT_PUBLIC_SITE_URL', 'not a url')

    expect(getSiteHost()).toBeNull()
  })
})
