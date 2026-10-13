import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

// SUPPORT_EMAIL is resolved once at module load (NEXT_PUBLIC_* is inlined at
// build time), so each case re-imports the module after stubbing the env.
async function loadSupport() {
  vi.resetModules()
  return import('../../lib/support')
}

beforeEach(() => {
  vi.stubEnv('NEXT_PUBLIC_SUPPORT_EMAIL', '')
})

afterEach(() => {
  vi.unstubAllEnvs()
})

describe('SUPPORT_EMAIL', () => {
  it('defaults to the owner-read inbox, never a blogai.com address', async () => {
    const { SUPPORT_EMAIL, DEFAULT_SUPPORT_EMAIL } = await loadSupport()

    expect(SUPPORT_EMAIL).toBe('support@lscaturchio.xyz')
    expect(SUPPORT_EMAIL).toBe(DEFAULT_SUPPORT_EMAIL)
    expect(SUPPORT_EMAIL).not.toMatch(/blogai\.com|blog-ai\.com/)
  })

  it('reads NEXT_PUBLIC_SUPPORT_EMAIL when set', async () => {
    vi.stubEnv('NEXT_PUBLIC_SUPPORT_EMAIL', '  help@example.test  ')
    const { SUPPORT_EMAIL } = await loadSupport()

    expect(SUPPORT_EMAIL).toBe('help@example.test')
  })
})

describe('supportMailto', () => {
  it('builds a mailto link with an encoded subject', async () => {
    const { supportMailto } = await loadSupport()

    expect(supportMailto()).toBe('mailto:support@lscaturchio.xyz')
    expect(supportMailto('Tool request: PDF export')).toBe(
      'mailto:support@lscaturchio.xyz?subject=Tool%20request%3A%20PDF%20export'
    )
  })
})
