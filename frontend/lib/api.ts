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

// API URLs from environment variables with fallbacks for development
// In production, these should be set to HTTPS URLs
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

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
} as const;

// Default headers for API requests
export const getDefaultHeaders = (): HeadersInit => {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };

  // Add API key if available
  const apiKey = process.env.NEXT_PUBLIC_API_KEY;
  if (apiKey) {
    headers['X-API-Key'] = apiKey;
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
      headers: getDefaultHeaders(),
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
export const apiFetch = async <T>(
  url: string,
  options: RequestInit = {}
): Promise<T> => {
  const response = await fetch(url, {
    ...options,
    headers: {
      ...getDefaultHeaders(),
      ...options.headers,
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }

  return response.json();
};
