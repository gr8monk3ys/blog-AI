/**
 * API configuration and utilities
 */

// API URLs from environment variables with fallbacks for development
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
export const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

// API endpoints
export const API_ENDPOINTS = {
  root: `${API_BASE_URL}/`,
  generateBlog: `${API_BASE_URL}/generate-blog`,
  generateBook: `${API_BASE_URL}/generate-book`,
  conversation: (id: string) => `${API_BASE_URL}/conversations/${id}`,
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
