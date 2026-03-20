import { describe, it, expect, vi, afterEach } from 'vitest'

describe('canServeDemoData', () => {
  afterEach(() => {
    vi.unstubAllEnvs()
    vi.resetModules()
  })

  it('returns false when DEMO_DATA_ENABLED is "false"', async () => {
    vi.stubEnv('DEMO_DATA_ENABLED', 'false')
    const { canServeDemoData } = await import('../../lib/server-mode')
    expect(canServeDemoData()).toBe(false)
  })

  it('returns true when DEMO_DATA_ENABLED is "true"', async () => {
    vi.stubEnv('DEMO_DATA_ENABLED', 'true')
    const { canServeDemoData } = await import('../../lib/server-mode')
    expect(canServeDemoData()).toBe(true)
  })

  it('defaults to true in non-production', async () => {
    vi.stubEnv('NODE_ENV', 'development')
    const { canServeDemoData } = await import('../../lib/server-mode')
    expect(canServeDemoData()).toBe(true)
  })
})
