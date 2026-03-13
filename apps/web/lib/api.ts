/**
 * API configuration and utilities
 */

/**
 * Determine if we're in a production environment based on URL or env var
 */
const isProduction = (): boolean => {
  if (typeof window !== 'undefined') {
    return window.location.protocol === 'https:';
  }
  return process.env.NODE_ENV === 'production';
};

/**
 * Get the appropriate WebSocket protocol based on HTTP protocol
 */
const getWsProtocol = (apiUrl: string): string => {
  if (apiUrl.startsWith('https://')) {
    return apiUrl.replace('https://', 'wss://');
  }
  if (apiUrl.startsWith('http://')) {
    return apiUrl.replace('http://', 'ws://');
  }
  // If no protocol, infer from environment
  return isProduction() ? `wss://${apiUrl}` : `ws://${apiUrl}`;
};

// API URLs from environment variables with fallbacks for development.
// In production without the env var, warn loudly but fall back to localhost
// so that `npm run build` still works locally.
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || (() => {
  if (process.env.NODE_ENV === 'production' && typeof window !== 'undefined') {
    console.error(
      '[api] NEXT_PUBLIC_API_URL is not set. ' +
      'API calls will fail. Set it to your backend URL (e.g. https://api.blogai.com).'
    )
  }
  return 'http://localhost:8000'
})()

// API version - can be overridden via environment variable
export const API_VERSION = process.env.NEXT_PUBLIC_API_VERSION || 'v1';

// Derive WebSocket URL from API URL if not explicitly set
// This ensures protocol consistency (HTTPS -> WSS, HTTP -> WS)
export const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_URL || getWsProtocol(API_BASE_URL);

// Versioned API base URL
export const API_V1_BASE_URL = `${API_BASE_URL}/api/${API_VERSION}`;

// API endpoints - using versioned paths for future compatibility
export const API_ENDPOINTS = {
  root: `${API_BASE_URL}/`,
  // Versioned endpoints (recommended for new integrations)
  generateBlog: `${API_V1_BASE_URL}/generate-blog`,
  generateBook: `${API_V1_BASE_URL}/generate-book`,
  conversation: (id: string) => `${API_V1_BASE_URL}/conversations/${id}`,
  // WebSocket remains at root level (version negotiation via protocol)
  websocket: (conversationId: string) => `${WS_BASE_URL}/ws/conversation/${conversationId}`,
  // Tools API endpoints
  tools: {
    list: `${API_V1_BASE_URL}/tools`,
    categories: `${API_V1_BASE_URL}/tools/categories`,
    stats: `${API_V1_BASE_URL}/tools/stats`,
    get: (toolId: string) => `${API_V1_BASE_URL}/tools/${toolId}`,
    execute: (toolId: string) => `${API_V1_BASE_URL}/tools/${toolId}/execute`,
    score: (toolId: string) => `${API_V1_BASE_URL}/tools/${toolId}/score`,
    scoreGeneric: `${API_V1_BASE_URL}/tools/score`,
    variations: (toolId: string) => `${API_V1_BASE_URL}/tools/${toolId}/variations`,
    validate: (toolId: string) => `${API_V1_BASE_URL}/tools/${toolId}/validate`,
    byCategory: (category: string) => `${API_V1_BASE_URL}/tools/category/${category}`,
  },
  // Bulk generation endpoints (legacy)
  bulk: {
    generate: `${API_V1_BASE_URL}/bulk/generate`,
    status: (jobId: string) => `${API_V1_BASE_URL}/bulk/status/${jobId}`,
    results: (jobId: string) => `${API_V1_BASE_URL}/bulk/results/${jobId}`,
    cancel: (jobId: string) => `${API_V1_BASE_URL}/bulk/cancel/${jobId}`,
  },
  // Enhanced batch generation endpoints (Tier 1)
  batch: {
    // Job management
    create: `${API_V1_BASE_URL}/batch`,
    list: `${API_V1_BASE_URL}/batch/jobs`,
    status: (jobId: string) => `${API_V1_BASE_URL}/batch/${jobId}`,
    results: (jobId: string) => `${API_V1_BASE_URL}/batch/${jobId}/results`,
    cancel: (jobId: string) => `${API_V1_BASE_URL}/batch/${jobId}/cancel`,
    retry: (jobId: string) => `${API_V1_BASE_URL}/batch/${jobId}/retry`,
    // CSV import/export
    importCsv: `${API_V1_BASE_URL}/batch/import/csv`,
    template: `${API_V1_BASE_URL}/batch/template/csv`,
    export: (jobId: string, format: string) => `${API_V1_BASE_URL}/batch/export/${jobId}?format=${format}`,
    // Cost estimation
    estimate: `${API_V1_BASE_URL}/batch/estimate`,
  },
  // Usage tracking endpoints
  usage: {
    // Quota-based subscription system (source of truth for SaaS billing/limits)
    stats: `${API_V1_BASE_URL}/usage/quota/stats`,
    check: `${API_V1_BASE_URL}/usage/quota/check`,
    tiers: `${API_V1_BASE_URL}/usage/quota/tiers`,
    breakdown: `${API_V1_BASE_URL}/usage/quota/breakdown`,
  },

  // Non-sensitive runtime config
  config: {
    llm: `${API_V1_BASE_URL}/config/llm`,
  },

  // Payments / Stripe endpoints
  payments: {
    checkout: `${API_BASE_URL}/api/payments/create-checkout-session`,
    portal: `${API_BASE_URL}/api/payments/create-portal-session`,
    pricing: `${API_BASE_URL}/api/payments/pricing`,
  },
  // Templates API endpoints
  templates: {
    list: '/api/templates',
    get: (id: string) => `/api/templates/${id}`,
    create: '/api/templates',
    update: (id: string) => `/api/templates/${id}`,
    delete: (id: string) => `/api/templates/${id}`,
    use: (id: string) => `/api/templates/${id}/use`,
  },
  // Brand Profiles API endpoints
  brandProfiles: {
    list: '/api/brand-profiles',
    get: (id: string) => `/api/brand-profiles/${id}`,
    create: '/api/brand-profiles',
    update: (id: string) => `/api/brand-profiles/${id}`,
    delete: (id: string) => `/api/brand-profiles/${id}`,
    setDefault: (id: string) => `/api/brand-profiles/${id}/default`,
  },
  // Content Remix API endpoints
  remix: {
    formats: `${API_V1_BASE_URL}/remix/formats`,
    format: (formatId: string) => `${API_V1_BASE_URL}/remix/formats/${formatId}`,
    analyze: `${API_V1_BASE_URL}/remix/analyze`,
    preview: `${API_V1_BASE_URL}/remix/preview`,
    transform: `${API_V1_BASE_URL}/remix/transform`,
    transformFormat: (formatId: string) => `${API_V1_BASE_URL}/remix/transform/${formatId}`,
    batch: `${API_V1_BASE_URL}/remix/batch`,
  },
  // Deep research endpoints
  research: {
    conduct: `${API_V1_BASE_URL}/research`,
    history: `${API_V1_BASE_URL}/research/history`,
    get: (queryId: string) => `${API_V1_BASE_URL}/research/${queryId}`,
  },
  // Content quality endpoints
  content: {
    checkPlagiarism: `${API_V1_BASE_URL}/content/check-plagiarism`,
    plagiarismQuota: `${API_V1_BASE_URL}/content/plagiarism/quota`,
  },
  // Brand Voice Training API endpoints
  brandVoice: {
    analyze: `${API_V1_BASE_URL}/brand-voice/analyze`,
    samples: `${API_V1_BASE_URL}/brand-voice/samples`,
    samplesByProfile: (profileId: string) => `${API_V1_BASE_URL}/brand-voice/samples/${profileId}`,
    deleteSample: (profileId: string, sampleId: string) => `${API_V1_BASE_URL}/brand-voice/samples/${profileId}/${sampleId}`,
    train: `${API_V1_BASE_URL}/brand-voice/train`,
    fingerprint: (profileId: string) => `${API_V1_BASE_URL}/brand-voice/fingerprint/${profileId}`,
    score: `${API_V1_BASE_URL}/brand-voice/score`,
    status: (profileId: string) => `${API_V1_BASE_URL}/brand-voice/status/${profileId}`,
  },
  // Content feedback endpoints
  feedback: {
    submit: '/api/feedback',
    stats: (contentId: string) => `/api/feedback?content_id=${encodeURIComponent(contentId)}`,
  },
  // Organization / team endpoints
  organizations: {
    list: `${API_V1_BASE_URL}/organizations`,
    create: `${API_V1_BASE_URL}/organizations`,
    get: (orgId: string) => `${API_V1_BASE_URL}/organizations/${orgId}`,
    members: (orgId: string) => `${API_V1_BASE_URL}/organizations/${orgId}/members`,
    invites: (orgId: string) => `${API_V1_BASE_URL}/organizations/${orgId}/invites`,
    invite: (orgId: string) => `${API_V1_BASE_URL}/organizations/${orgId}/invites`,
    updateMember: (orgId: string, userId: string) =>
      `${API_V1_BASE_URL}/organizations/${orgId}/members/${userId}`,
    removeMember: (orgId: string, userId: string) =>
      `${API_V1_BASE_URL}/organizations/${orgId}/members/${userId}`,
  },
  // Content editing endpoints
  editSection: `${API_BASE_URL}/edit-section`,
  saveBook: `${API_BASE_URL}/save-book`,
  downloadBook: `${API_BASE_URL}/download-book`,
} as const;

// Default headers for API requests
export const getDefaultHeaders = async (): Promise<HeadersInit> => {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };

  // In the cloud SaaS, clients authenticate with Clerk session JWTs.
  // We attach the current session token as `Authorization: Bearer ...` so the
  // backend (Railway) can verify it.
  if (typeof window !== 'undefined') {
    try {
      // Clerk injects a global `window.Clerk` when configured.
      const clerk = (
        window as Window & {
          Clerk?: {
            session?: {
              getToken?: () => Promise<string | null>
            }
          }
        }
      ).Clerk
      if (clerk?.session?.getToken) {
        const token = await clerk.session.getToken()
        if (token) headers['Authorization'] = `Bearer ${token}`
      }
    } catch {
      // Ignore auth header if Clerk is not configured or session is unavailable.
    }
  }

  // Local-only fallback for realistic end-to-end testing without Clerk.
  // Never attach a static public API key in production.
  if (
    !('Authorization' in headers) &&
    process.env.NODE_ENV !== 'production' &&
    process.env.NEXT_PUBLIC_API_KEY
  ) {
    headers['X-API-Key'] = process.env.NEXT_PUBLIC_API_KEY
  }

  return headers;
};

/**
 * Check if the backend server is running
 */
export const checkServerConnection = async (): Promise<boolean> => {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 2000);

    const response = await fetch(API_ENDPOINTS.root, {
      signal: controller.signal,
      headers: await getDefaultHeaders(),
    });

    clearTimeout(timeoutId);
    return response.ok;
  } catch (err) {
    console.log('Server connection check failed:', err);
    return false;
  }
};

/**
 * Generic API fetch wrapper with error handling
 */
export class ApiError extends Error {
  status: number
  data: unknown

  constructor(message: string, status: number, data: unknown) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.data = data
  }
}

function extractErrorMessage(errorData: unknown, status: number): string {
  if (typeof errorData === 'string') return errorData

  if (errorData && typeof errorData === 'object') {
    const obj = errorData as Record<string, unknown>
    const detail = obj?.detail

    // FastAPI HTTPException: { detail: "..." }
    if (typeof detail === 'string') return detail

    // FastAPI validation errors: { detail: [{ msg: "..." }, ...] }
    if (Array.isArray(detail) && detail.length > 0) {
      const first = detail[0] as Record<string, unknown> | undefined
      if (first && typeof first.msg === 'string') {
        return first.msg
      }
    }

    // QuotaExceededError is returned as { detail: { error: "..." } }
    if (detail && typeof detail === 'object') {
      const nestedDetail = detail as Record<string, unknown>
      if (typeof nestedDetail.error === 'string') return nestedDetail.error
      if (typeof nestedDetail.message === 'string') return nestedDetail.message
    }

    // Custom JSON errors: { error: "..." } or { message: "..." }
    if (typeof obj.error === 'string') return obj.error
    if (typeof obj.message === 'string') return obj.message
  }

  return `HTTP error! status: ${status}`
}

export const apiFetch = async <T>(
  url: string,
  options: RequestInit = {}
): Promise<T> => {
  const defaultHeaders = await getDefaultHeaders()
  const response = await fetch(url, {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    const message = extractErrorMessage(errorData, response.status)
    throw new ApiError(message, response.status, errorData)
  }

  return response.json();
};

/**
 * HTTP status codes that are safe to retry (server/gateway issues).
 * Client errors (4xx) are NOT retried since the request itself is wrong.
 */
const RETRYABLE_STATUS_CODES = new Set([502, 503, 504])

/**
 * Check if an error is a network-level failure (e.g. DNS, connection refused).
 */
function isNetworkError(err: unknown): boolean {
  return err instanceof TypeError && err.message.toLowerCase().includes('fetch')
}

/**
 * API fetch wrapper with exponential backoff retry for transient failures.
 *
 * Retries up to `maxRetries` times on 502, 503, 504, and network errors.
 * Does NOT retry on 4xx client errors (400, 401, 403, 404, 429, etc.).
 *
 * Use this for long-running generation endpoints where transient gateway
 * failures are expected.
 */
export const apiFetchWithRetry = async <T>(
  url: string,
  options: RequestInit = {},
  maxRetries = 3
): Promise<T> => {
  let lastError: unknown

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await apiFetch<T>(url, options)
    } catch (err) {
      lastError = err

      // Only retry on retryable status codes or network errors
      const isRetryable =
        (err instanceof ApiError && RETRYABLE_STATUS_CODES.has(err.status)) ||
        isNetworkError(err)

      if (!isRetryable || attempt >= maxRetries) {
        throw err
      }

      // Exponential backoff: 1s, 2s, 4s
      const delayMs = 1000 * Math.pow(2, attempt)
      await new Promise((resolve) => setTimeout(resolve, delayMs))
    }
  }

  // This is unreachable but satisfies TypeScript
  throw lastError
};
