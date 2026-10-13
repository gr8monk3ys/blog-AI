// @vitest-environment node
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import pkg from '../../../package.json'

const mockQuery = vi.fn()
const mockGetSqlOrNull = vi.fn()

vi.mock('../../../lib/db', () => ({
  getSqlOrNull: () => mockGetSqlOrNull(),
}))

import { GET } from '../../../app/api/health/route'

const ENV_KEYS = [
  'DATABASE_URL',
  'NEXT_PUBLIC_API_URL',
  'NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY',
  'CLERK_SECRET_KEY',
  'NEXT_PUBLIC_CLERK_DOMAIN',
  'NEXT_PUBLIC_APP_VERSION',
  'VERCEL_GIT_COMMIT_SHA',
  'VERCEL_ENV',
] as const

const healthyUpstream = {
  status: 'healthy',
  version: '0.1.0',
  services: {
    database: { status: 'connected', latency_ms: 4 },
    redis: { status: 'disconnected', latency_ms: null },
    llm_providers: {
      openai: { configured: true, model: 'gpt-4o' },
      anthropic: { configured: true, model: 'claude' },
      gemini: { configured: false, model: null },
    },
  },
  features: {
    content_generation: { available: true, note: null },
    web_research: { available: false, note: 'Requires SERP_API_KEY or TAVILY_API_KEY' },
  },
}

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

const fetchMock = vi.fn<typeof fetch>()

beforeEach(() => {
  vi.clearAllMocks()
  for (const key of ENV_KEYS) vi.stubEnv(key, '')
  vi.stubGlobal('fetch', fetchMock)
  mockGetSqlOrNull.mockReturnValue(null)
  mockQuery.mockResolvedValue([{ '?column?': 1 }])
})

afterEach(() => {
  vi.unstubAllEnvs()
  vi.unstubAllGlobals()
})

function configureDb() {
  mockGetSqlOrNull.mockReturnValue({ query: mockQuery })
}

describe('GET /api/health', () => {
  it('skips every unconfigured dependency and answers 200', async () => {
    const res = await GET()
    const body = await res.json()

    expect(res.status).toBe(200)
    expect(res.headers.get('cache-control')).toBe('no-store')
    expect(body.status).toBe('ok')
    expect(body.checks.db).toEqual({ status: 'skipped' })
    expect(body.checks.api).toEqual({ status: 'skipped' })
    expect(body.checks.clerk.status).toBe('skipped')
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('reports the package version, and the Vercel commit when present', async () => {
    vi.stubEnv('VERCEL_GIT_COMMIT_SHA', 'abc1234')
    vi.stubEnv('VERCEL_ENV', 'production')

    const body = await (await GET()).json()

    expect(body.version).toBe(pkg.version)
    expect(body.commit).toBe('abc1234')
    expect(body.environment).toBe('production')
  })

  it('prefers NEXT_PUBLIC_APP_VERSION over package.json', async () => {
    vi.stubEnv('NEXT_PUBLIC_APP_VERSION', '9.9.9')

    expect((await (await GET()).json()).version).toBe('9.9.9')
  })

  it('runs SELECT 1 through lib/db when a database is configured', async () => {
    configureDb()

    const body = await (await GET()).json()

    expect(mockQuery).toHaveBeenCalledWith('SELECT 1')
    expect(body.checks.db.status).toBe('ok')
    expect(typeof body.checks.db.latencyMs).toBe('number')
  })

  it('answers 503 when the configured database is unreachable', async () => {
    configureDb()
    mockQuery.mockRejectedValue(new Error('connection refused'))

    const res = await GET()
    const body = await res.json()

    expect(res.status).toBe(503)
    expect(body.status).toBe('error')
    expect(body.checks.db).toMatchObject({ status: 'error', error: 'connection refused' })
  })

  it('probes the API and summarises its services and features', async () => {
    vi.stubEnv('NEXT_PUBLIC_API_URL', 'https://api.example.test/')
    fetchMock.mockResolvedValue(jsonResponse(healthyUpstream))

    const res = await GET()
    const body = await res.json()

    expect(fetchMock).toHaveBeenCalledTimes(1)
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toBe('https://api.example.test/health')
    expect(init.cache).toBe('no-store')
    expect(init.signal).toBeInstanceOf(AbortSignal)

    expect(res.status).toBe(200)
    expect(body.checks.api).toMatchObject({
      status: 'ok',
      httpStatus: 200,
      upstreamStatus: 'healthy',
      version: '0.1.0',
      services: {
        database: 'connected',
        redis: 'disconnected',
        llmProviders: ['openai', 'anthropic'],
      },
      features: { content_generation: true, web_research: false },
    })
    expect(typeof body.checks.api.latencyMs).toBe('number')
  })

  it('answers 503 when the API reports anything but healthy', async () => {
    vi.stubEnv('NEXT_PUBLIC_API_URL', 'https://api.example.test')
    fetchMock.mockResolvedValue(jsonResponse({ ...healthyUpstream, status: 'degraded' }))

    const res = await GET()
    const body = await res.json()

    expect(res.status).toBe(503)
    expect(body.checks.api).toMatchObject({
      status: 'error',
      upstreamStatus: 'degraded',
      error: 'upstream reports degraded',
    })
  })

  it('answers 503 when the API returns a non-2xx status', async () => {
    vi.stubEnv('NEXT_PUBLIC_API_URL', 'https://api.example.test')
    fetchMock.mockResolvedValue(new Response('Bad Gateway', { status: 502 }))

    const res = await GET()
    const body = await res.json()

    expect(res.status).toBe(503)
    expect(body.checks.api).toMatchObject({ status: 'error', httpStatus: 502, error: 'HTTP 502' })
  })

  it('answers 503 and names the timeout when the API does not respond', async () => {
    vi.stubEnv('NEXT_PUBLIC_API_URL', 'https://api.example.test')
    const timeout = new Error('The operation was aborted due to timeout')
    timeout.name = 'TimeoutError'
    fetchMock.mockRejectedValue(timeout)

    const res = await GET()
    const body = await res.json()

    expect(res.status).toBe(503)
    expect(body.checks.api).toMatchObject({ status: 'error', error: 'timeout' })
  })

  it('reports Clerk as configured with booleans only', async () => {
    vi.stubEnv('NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY', 'pk_live_secretvalue')
    vi.stubEnv('CLERK_SECRET_KEY', 'sk_live_secretvalue')
    vi.stubEnv('NEXT_PUBLIC_CLERK_DOMAIN', 'clerk.example.test')

    const res = await GET()
    const text = await res.text()
    const body = JSON.parse(text)

    expect(body.checks.clerk).toEqual({
      status: 'ok',
      configured: true,
      publishableKey: true,
      secretKey: true,
      customDomain: true,
    })
    expect(text).not.toContain('secretvalue')
    expect(text).not.toContain('clerk.example.test')
  })

  it('flags a half-configured Clerk as an error', async () => {
    vi.stubEnv('NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY', 'pk_test_only')

    const res = await GET()
    const body = await res.json()

    expect(res.status).toBe(503)
    expect(body.checks.clerk).toMatchObject({ status: 'error', configured: false, publishableKey: true, secretKey: false })
  })
})
