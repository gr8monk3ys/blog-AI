import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import {
  API_BASE_URL,
  API_V1_BASE_URL,
  WS_BASE_URL,
  API_ENDPOINTS,
  getDefaultHeaders,
  checkServerConnection,
  apiFetch,
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
  })

  describe('getDefaultHeaders', () => {
    it('should return Content-Type header', async () => {
      const headers = (await getDefaultHeaders()) as Record<string, string>
      expect(headers['Content-Type']).toBe('application/json')
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
