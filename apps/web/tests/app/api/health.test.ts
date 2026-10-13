// @vitest-environment node
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import pkg from '../../../package.json'

const mockQuery = vi.fn()
const mockGetSqlOrNull = vi.fn()

vi.mock('../../../lib/db', () => ({
  getSqlOrNull: () => mockGetSqlOrNull(),
}))

import { GET, isDetailAuthorised } from '../../../app/api/health/route'

const ENV_KEYS = [
  'DATABASE_URL',
  'NEXT_PUBLIC_API_URL',
  'NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY',
  'CLERK_SECRET_KEY',
  'NEXT_PUBLIC_CLERK_DOMAIN',
  'NEXT_PUBLIC_APP_VERSION',
  'VERCEL_GIT_COMMIT_SHA',
  'VERCEL_ENV',
  'HEALTH_DETAIL_TOKEN',
] as const

const DETAIL_TOKEN = 'detail-token-for-tests'

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

const request = (authorization?: string) =>
  new Request('http://localhost/api/health', authorization ? { headers: { authorization } } : undefined)

const get = (authorization?: string) => GET(request(authorization))

/** Anything that looks like an environment variable name. */
const ENV_NAME = /\b[A-Z][A-Z0-9]*_[A-Z0-9_]+\b/

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

function configureEverything() {
  configureDb()
  vi.stubEnv('NEXT_PUBLIC_API_URL', 'https://api.example.test/')
  vi.stubEnv('NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY', 'pk_live_secretvalue')
  vi.stubEnv('CLERK_SECRET_KEY', 'sk_live_secretvalue')
  vi.stubEnv('NEXT_PUBLIC_CLERK_DOMAIN', 'clerk.example.test')
  fetchMock.mockResolvedValue(jsonResponse(healthyUpstream))
}

describe('GET /api/health (public)', () => {
  it('reports unconfigured dependencies as degraded, with 200', async () => {
    const res = await get()
    const body = await res.json()

    expect(res.status).toBe(200)
    expect(res.headers.get('cache-control')).toBe('no-store')
    expect(body.status).toBe('degraded')
    expect(body.checks).toEqual({
      db: { status: 'degraded' },
      api: { status: 'degraded' },
      clerk: { status: 'degraded' },
    })
    expect(body.details).toBeUndefined()
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('is ok with 200 when every dependency answers', async () => {
    configureEverything()

    const res = await get()
    const body = await res.json()

    expect(res.status).toBe(200)
    expect(body.status).toBe('ok')
    expect(body.checks.db.status).toBe('ok')
    expect(typeof body.checks.db.latencyMs).toBe('number')
    expect(body.checks.api).toMatchObject({ status: 'ok', version: '0.1.0' })
    expect(body.checks.clerk).toEqual({ status: 'ok' })
    expect(mockQuery).toHaveBeenCalledWith('SELECT 1')
  })

  it('never names an environment variable, key, provider or error in the public body', async () => {
    configureEverything()
    mockQuery.mockRejectedValue(new Error('connection to host db.example.test refused; DATABASE_URL invalid'))
    vi.stubEnv('CLERK_SECRET_KEY', '') // half-configured Clerk
    fetchMock.mockResolvedValue(jsonResponse({ ...healthyUpstream, status: 'degraded' }))

    const res = await get()
    const text = await res.text()
    const body = JSON.parse(text)

    expect(res.status).toBe(503)
    expect(body.details).toBeUndefined()
    expect(text).not.toMatch(ENV_NAME)
    for (const forbidden of ['secretvalue', 'pk_live', 'sk_live', 'openai', 'anthropic', 'gemini', 'redis', 'web_research', 'refused', 'db.example.test', 'clerk.example.test', 'publishableKey', 'secretKey', 'configured', 'error', 'upstream', 'healthy']) {
      expect(text).not.toContain(forbidden)
    }
    // Only aggregate words appear.
    expect(Object.keys(body.checks.db).sort()).toEqual(['latencyMs', 'status'])
    expect(Object.keys(body.checks.clerk)).toEqual(['status'])
  })

  it('reports the package version, and the Vercel commit when present', async () => {
    vi.stubEnv('VERCEL_GIT_COMMIT_SHA', 'abc1234')
    vi.stubEnv('VERCEL_ENV', 'production')

    const body = await (await get()).json()

    expect(body.version).toBe(pkg.version)
    expect(body.commit).toBe('abc1234')
    expect(body.environment).toBe('production')
  })

  it('prefers NEXT_PUBLIC_APP_VERSION over package.json', async () => {
    vi.stubEnv('NEXT_PUBLIC_APP_VERSION', '9.9.9')

    expect((await (await get()).json()).version).toBe('9.9.9')
  })

  it('answers 503 and down when the configured database is unreachable', async () => {
    configureDb()
    mockQuery.mockRejectedValue(new Error('connection refused'))

    const res = await get()
    const body = await res.json()

    expect(res.status).toBe(503)
    expect(body.status).toBe('down')
    expect(body.checks.db.status).toBe('down')
    expect(body.checks.db.error).toBeUndefined()
  })

  it('probes the API with a timeout and no-store', async () => {
    vi.stubEnv('NEXT_PUBLIC_API_URL', 'https://api.example.test/')
    fetchMock.mockResolvedValue(jsonResponse(healthyUpstream))

    await get()

    expect(fetchMock).toHaveBeenCalledTimes(1)
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toBe('https://api.example.test/health')
    expect(init.cache).toBe('no-store')
    expect(init.signal).toBeInstanceOf(AbortSignal)
  })

  it('is degraded (200) when the API answers 2xx but not healthy', async () => {
    vi.stubEnv('NEXT_PUBLIC_API_URL', 'https://api.example.test')
    fetchMock.mockResolvedValue(jsonResponse({ ...healthyUpstream, status: 'degraded' }))

    const res = await get()
    const body = await res.json()

    expect(res.status).toBe(200)
    expect(body.status).toBe('degraded')
    expect(body.checks.api.status).toBe('degraded')
  })

  it('is down (503) when the API returns a non-2xx status', async () => {
    vi.stubEnv('NEXT_PUBLIC_API_URL', 'https://api.example.test')
    fetchMock.mockResolvedValue(new Response('Bad Gateway', { status: 502 }))

    const res = await get()
    const body = await res.json()

    expect(res.status).toBe(503)
    expect(body.checks.api).toEqual({ status: 'down', latencyMs: expect.any(Number) })
  })

  it('is down (503) when the API does not respond in time', async () => {
    vi.stubEnv('NEXT_PUBLIC_API_URL', 'https://api.example.test')
    const timeout = new Error('The operation was aborted due to timeout')
    timeout.name = 'TimeoutError'
    fetchMock.mockRejectedValue(timeout)

    const res = await get()

    expect(res.status).toBe(503)
    expect((await res.json()).checks.api.status).toBe('down')
  })

  it('treats a half-configured Clerk as down', async () => {
    vi.stubEnv('NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY', 'pk_test_only')

    const res = await get()
    const body = await res.json()

    expect(res.status).toBe(503)
    expect(body.checks.clerk).toEqual({ status: 'down' })
  })
})

describe('GET /api/health (detail view)', () => {
  it('has no detail view when HEALTH_DETAIL_TOKEN is unset, whatever is presented', async () => {
    configureEverything()

    const body = await (await get('Bearer anything')).json()

    expect(body.details).toBeUndefined()
  })

  it('ignores a wrong or malformed token', async () => {
    configureEverything()
    vi.stubEnv('HEALTH_DETAIL_TOKEN', DETAIL_TOKEN)

    expect((await (await get('Bearer wrong-token-for-tests')).json()).details).toBeUndefined()
    expect((await (await get('Bearer short')).json()).details).toBeUndefined()
    expect((await (await get(DETAIL_TOKEN)).json()).details).toBeUndefined()
    expect((await (await get()).json()).details).toBeUndefined()
  })

  it('adds details for the right bearer token', async () => {
    configureEverything()
    vi.stubEnv('HEALTH_DETAIL_TOKEN', DETAIL_TOKEN)
    mockQuery.mockRejectedValue(new Error('connection refused'))
    fetchMock.mockResolvedValue(jsonResponse({ ...healthyUpstream, status: 'degraded' }))

    const res = await get(`Bearer ${DETAIL_TOKEN}`)
    const text = await res.text()
    const body = JSON.parse(text)

    expect(body.details).toEqual({
      db: { configured: true, error: 'connection refused' },
      api: {
        configured: true,
        httpStatus: 200,
        upstreamStatus: 'degraded',
        error: 'upstream reports degraded',
        services: { database: 'connected', redis: 'disconnected', llmProviders: ['openai', 'anthropic'] },
        features: { content_generation: true, web_research: false },
      },
      clerk: { publishableKey: true, secretKey: true, customDomain: true },
    })
    // Even the detail view reports presence, never values.
    expect(text).not.toContain('secretvalue')
    expect(text).not.toContain(DETAIL_TOKEN)
  })
})

describe('isDetailAuthorised', () => {
  it('compares in constant time and tolerates length mismatches', () => {
    expect(isDetailAuthorised('Bearer abc', 'abc')).toBe(true)
    expect(isDetailAuthorised('bearer   abc  ', 'abc')).toBe(true)
    expect(isDetailAuthorised('Bearer abcd', 'abc')).toBe(false)
    expect(isDetailAuthorised('Bearer ab', 'abc')).toBe(false)
    expect(isDetailAuthorised('Basic abc', 'abc')).toBe(false)
    expect(isDetailAuthorised(null, 'abc')).toBe(false)
    expect(isDetailAuthorised('Bearer abc', undefined)).toBe(false)
    expect(isDetailAuthorised('Bearer abc', '   ')).toBe(false)
  })
})
