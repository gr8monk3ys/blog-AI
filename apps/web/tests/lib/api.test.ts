import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import {
  API_BASE_URL,
  API_V1_BASE_URL,
  WS_BASE_URL,
  API_ENDPOINTS,
  ApiError,
  getDefaultHeaders,
  checkServerConnection,
  apiFetch,
  apiFetchWithRetry,
} from '../../lib/api'

describe('API Configuration', () => {
  describe('API_ENDPOINTS', () => {
    it('should have correct root endpoint', () => {
      expect(API_ENDPOINTS.root).toBe(`${API_BASE_URL}/`)
    })

    it('should have correct generateBlog endpoint', () => {
      expect(API_ENDPOINTS.generateBlog).toBe(`${API_V1_BASE_URL}/generate-blog`)
    })

    it('should have correct generateBook endpoint', () => {
      expect(API_ENDPOINTS.generateBook).toBe(`${API_V1_BASE_URL}/generate-book`)
    })

    it('should generate correct conversation endpoint', () => {
      const conversationId = 'test-123'
      expect(API_ENDPOINTS.conversation(conversationId)).toBe(
        `${API_V1_BASE_URL}/conversations/${conversationId}`
      )
    })

    it('should generate correct websocket endpoint', () => {
      const conversationId = 'test-456'
      expect(API_ENDPOINTS.websocket(conversationId)).toBe(
        `${WS_BASE_URL}/ws/conversation/${conversationId}`
      )
    })

    it('should generate all dynamic endpoint routes', () => {
      const id = 'id-123'
      const category = 'blog'
      const sampleId = 'sample-1'

      expect(API_ENDPOINTS.tools.get(id)).toContain(`/tools/${id}`)
      expect(API_ENDPOINTS.tools.execute(id)).toContain(`/tools/${id}/execute`)
      expect(API_ENDPOINTS.tools.score(id)).toContain(`/tools/${id}/score`)
      expect(API_ENDPOINTS.tools.variations(id)).toContain(`/tools/${id}/variations`)
      expect(API_ENDPOINTS.tools.validate(id)).toContain(`/tools/${id}/validate`)
      expect(API_ENDPOINTS.tools.byCategory(category)).toContain(`/tools/category/${category}`)

      expect(API_ENDPOINTS.bulk.status(id)).toContain(`/bulk/status/${id}`)
      expect(API_ENDPOINTS.bulk.results(id)).toContain(`/bulk/results/${id}`)
      expect(API_ENDPOINTS.bulk.cancel(id)).toContain(`/bulk/cancel/${id}`)

      expect(API_ENDPOINTS.batch.status(id)).toContain(`/batch/${id}`)
      expect(API_ENDPOINTS.batch.results(id)).toContain(`/batch/${id}/results`)
      expect(API_ENDPOINTS.batch.cancel(id)).toContain(`/batch/${id}/cancel`)
      expect(API_ENDPOINTS.batch.retry(id)).toContain(`/batch/${id}/retry`)
      expect(API_ENDPOINTS.batch.export(id, 'csv')).toContain(`/batch/export/${id}?format=csv`)

      expect(API_ENDPOINTS.templates.get(id)).toBe(`/api/templates/${id}`)
      expect(API_ENDPOINTS.templates.update(id)).toBe(`/api/templates/${id}`)
      expect(API_ENDPOINTS.templates.delete(id)).toBe(`/api/templates/${id}`)
      expect(API_ENDPOINTS.templates.use(id)).toBe(`/api/templates/${id}/use`)

      expect(API_ENDPOINTS.brandProfiles.get(id)).toBe(`/api/brand-profiles/${id}`)
      expect(API_ENDPOINTS.brandProfiles.update(id)).toBe(`/api/brand-profiles/${id}`)
      expect(API_ENDPOINTS.brandProfiles.delete(id)).toBe(`/api/brand-profiles/${id}`)
      expect(API_ENDPOINTS.brandProfiles.setDefault(id)).toBe(`/api/brand-profiles/${id}/default`)

      expect(API_ENDPOINTS.remix.format(id)).toContain(`/remix/formats/${id}`)
      expect(API_ENDPOINTS.remix.transformFormat(id)).toContain(`/remix/transform/${id}`)

      expect(API_ENDPOINTS.feedback.stats(id)).toContain(`content_id=${encodeURIComponent(id)}`)

      expect(API_ENDPOINTS.brandVoice.samplesByProfile(id)).toContain(`/brand-voice/samples/${id}`)
      expect(API_ENDPOINTS.brandVoice.deleteSample(id, sampleId)).toContain(
        `/brand-voice/samples/${id}/${sampleId}`
      )
      expect(API_ENDPOINTS.brandVoice.fingerprint(id)).toContain(`/brand-voice/fingerprint/${id}`)
      expect(API_ENDPOINTS.brandVoice.status(id)).toContain(`/brand-voice/status/${id}`)
    })
  })

  describe('getDefaultHeaders', () => {
    it('should return Content-Type header', async () => {
      const headers = (await getDefaultHeaders()) as Record<string, string>
      expect(headers['Content-Type']).toBe('application/json')
    })

    it('should include Clerk bearer token when available', async () => {
      Object.defineProperty(window, 'Clerk', {
        configurable: true,
        value: {
          session: {
            getToken: vi.fn().mockResolvedValue('token-123'),
          },
        },
      })

      const headers = (await getDefaultHeaders()) as Record<string, string>
      expect(headers['Authorization']).toBe('Bearer token-123')
    })
  })
})

describe('checkServerConnection', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  it('should return true when server responds with ok', async () => {
    vi.mocked(global.fetch).mockResolvedValueOnce({
      ok: true,
    } as Response)

    const result = await checkServerConnection()
    expect(result).toBe(true)
  })

  it('should return false when server responds with error', async () => {
    vi.mocked(global.fetch).mockResolvedValueOnce({
      ok: false,
    } as Response)

    const result = await checkServerConnection()
    expect(result).toBe(false)
  })

  it('should return false when fetch throws error', async () => {
    vi.mocked(global.fetch).mockRejectedValueOnce(new Error('Network error'))

    const result = await checkServerConnection()
    expect(result).toBe(false)
  })

  it('should call fetch with correct endpoint', async () => {
    vi.mocked(global.fetch).mockResolvedValueOnce({
      ok: true,
    } as Response)

    await checkServerConnection()

    expect(global.fetch).toHaveBeenCalledWith(
      API_ENDPOINTS.root,
      expect.objectContaining({
        signal: expect.any(AbortSignal),
        headers: expect.objectContaining({
          'Content-Type': 'application/json',
        }),
      })
    )
  })
})

describe('apiFetch', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('should return JSON data on successful response', async () => {
    const mockData = { success: true, data: 'test' }
    vi.mocked(global.fetch).mockResolvedValueOnce({
      ok: true,
      json: vi.fn().mockResolvedValueOnce(mockData),
    } as unknown as Response)

    const result = await apiFetch('/test')
    expect(result).toEqual(mockData)
  })

  it('should throw error on non-ok response', async () => {
    vi.mocked(global.fetch).mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: vi.fn().mockResolvedValueOnce({ detail: 'Server error' }),
    } as unknown as Response)

    await expect(apiFetch('/test')).rejects.toThrow('Server error')
  })

  it('should throw generic error when response has no detail', async () => {
    vi.mocked(global.fetch).mockResolvedValueOnce({
      ok: false,
      status: 404,
      json: vi.fn().mockResolvedValueOnce({}),
    } as unknown as Response)

    await expect(apiFetch('/test')).rejects.toThrow('HTTP error! status: 404')
  })

  it('should extract validation message from detail array', async () => {
    vi.mocked(global.fetch).mockResolvedValueOnce({
      ok: false,
      status: 422,
      json: vi.fn().mockResolvedValueOnce({
        detail: [{ msg: 'Field is required' }],
      }),
    } as unknown as Response)

    await expect(apiFetch('/test')).rejects.toThrow('Field is required')
  })

  it('should extract message from nested detail object', async () => {
    vi.mocked(global.fetch).mockResolvedValueOnce({
      ok: false,
      status: 429,
      json: vi.fn().mockResolvedValueOnce({
        detail: { error: 'Rate limit reached' },
      }),
    } as unknown as Response)

    await expect(apiFetch('/test')).rejects.toThrow('Rate limit reached')
  })

  it('should merge custom headers with default headers', async () => {
    const mockData = { success: true }
    vi.mocked(global.fetch).mockResolvedValueOnce({
      ok: true,
      json: vi.fn().mockResolvedValueOnce(mockData),
    } as unknown as Response)

    await apiFetch('/test', {
      headers: { 'X-Custom-Header': 'custom-value' },
    })

    expect(global.fetch).toHaveBeenCalledWith(
      '/test',
      expect.objectContaining({
        headers: expect.objectContaining({
          'Content-Type': 'application/json',
          'X-Custom-Header': 'custom-value',
        }),
      })
    )
  })
})

describe('apiFetchWithRetry', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.restoreAllMocks()
    vi.mocked(global.fetch).mockReset()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('should retry on 503 and eventually succeed', async () => {
    vi.mocked(global.fetch)
      .mockResolvedValueOnce({
        ok: false,
        status: 503,
        json: vi.fn().mockResolvedValueOnce({ detail: 'Service unavailable' }),
      } as unknown as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: vi.fn().mockResolvedValueOnce({ success: true }),
      } as unknown as Response)

    const promise = apiFetchWithRetry('/retry', {}, 1)
    await vi.runAllTimersAsync()

    await expect(promise).resolves.toEqual({ success: true })
    expect(global.fetch).toHaveBeenCalledTimes(2)
  })

  it('should not retry on 400 errors', async () => {
    vi.mocked(global.fetch).mockResolvedValueOnce({
      ok: false,
      status: 400,
      json: vi.fn().mockResolvedValueOnce({ detail: 'Bad request' }),
    } as unknown as Response)

    await expect(apiFetchWithRetry('/no-retry', {}, 2)).rejects.toThrow(ApiError)
    expect(global.fetch).toHaveBeenCalledTimes(1)
  })
})
