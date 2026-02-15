/**
 * Blog AI Chrome Extension - API Client
 *
 * Handles all API communication with the Blog AI backend.
 * Includes authentication, content generation, and error handling.
 */

/**
 * Blog AI API Client
 */
const BlogAI = {
  /**
   * Default configuration
   */
  config: {
    // Production endpoint
    baseUrl: 'https://api.blogai.com',
    // Development endpoint (for local testing)
    devUrl: 'http://localhost:8000',
    // Request timeout in milliseconds
    timeout: 60000,
    // API version
    version: 'v1',
  },

  /**
   * Get the API base URL
   * @returns {Promise<string>} API base URL
   */
  async getBaseUrl() {
    try {
      const { settings } = await chrome.storage.sync.get(['settings'])
      if (settings && settings.apiEndpoint) {
        return settings.apiEndpoint
      }
    } catch (error) {
      console.error('[Blog AI API] Failed to get settings:', error)
    }
    return this.config.baseUrl
  },

  /**
   * Make an API request
   * @param {string} endpoint - API endpoint
   * @param {Object} options - Fetch options
   * @param {string} apiKey - API key
   * @returns {Promise<Object>} Response data
   */
  async request(endpoint, options = {}, apiKey = null) {
    const baseUrl = await this.getBaseUrl()
    const url = `${baseUrl}${endpoint}`

    const headers = {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    }

    if (apiKey) {
      headers['X-API-Key'] = apiKey
    }

    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), this.config.timeout)

    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          ...headers,
          ...options.headers,
        },
        signal: controller.signal,
      })

      clearTimeout(timeoutId)

      // Parse response
      let data
      const contentType = response.headers.get('content-type')

      if (contentType && contentType.includes('application/json')) {
        data = await response.json()
      } else {
        data = await response.text()
      }

      // Handle error responses
      if (!response.ok) {
        return {
          success: false,
          error: data.detail || data.error || `Request failed with status ${response.status}`,
          status: response.status,
        }
      }

      return {
        success: true,
        data: data,
        status: response.status,
      }
    } catch (error) {
      clearTimeout(timeoutId)

      if (error.name === 'AbortError') {
        return {
          success: false,
          error: 'Request timed out. Please try again.',
          status: 408,
        }
      }

      console.error('[Blog AI API] Request failed:', error)

      return {
        success: false,
        error: error.message || 'Network error. Please check your connection.',
        status: 0,
      }
    }
  },

  /**
   * Verify API key and get user info
   * @param {string} apiKey - API key to verify
   * @returns {Promise<Object>} Verification result
   */
  async verifyApiKey(apiKey) {
    if (!apiKey || typeof apiKey !== 'string') {
      return {
        success: false,
        error: 'Invalid API key format',
      }
    }

    return await this.request('/extension/auth', {
      method: 'POST',
      body: JSON.stringify({ api_key: apiKey }),
    })
  },

  /**
   * Get user info
   * @param {string} apiKey - API key
   * @returns {Promise<Object>} User info
   */
  async getUserInfo(apiKey) {
    return await this.request('/extension/user', {
      method: 'GET',
    }, apiKey)
  },

  /**
   * Generate content
   * @param {string} apiKey - API key
   * @param {Object} options - Generation options
   * @returns {Promise<Object>} Generated content
   */
  async generateContent(apiKey, options) {
    if (!apiKey) {
      return {
        success: false,
        error: 'API key is required',
      }
    }

    if (!options || !options.topic) {
      return {
        success: false,
        error: 'Topic is required',
      }
    }

    // Map length to approximate word count
    const lengthMap = {
      short: 500,
      medium: 1000,
      long: 2000,
    }

    const payload = {
      topic: options.topic,
      tone: options.tone || 'professional',
      target_length: lengthMap[options.length] || 1000,
      keywords: options.keywords || [],
      research: options.research || false,
      proofread: options.proofread || true,
      action: options.action || 'blog',
      provider_type: options.providerType || options.provider_type || undefined,
    }

    const response = await this.request('/extension/generate', {
      method: 'POST',
      body: JSON.stringify(payload),
    }, apiKey)

    if (!response.success) return response

    // Backend returns { success: true, data: {...} }. Unwrap for extension UIs.
    if (response.data && typeof response.data === 'object') {
      const body = response.data
      if (body.success === false) {
        return {
          success: false,
          error: body.error || 'Generation failed',
          status: response.status,
        }
      }
      if (body.data) {
        return {
          success: true,
          data: body.data,
          status: response.status,
        }
      }
    }

    return response
  },

  /**
   * Generate blog post
   * @param {string} apiKey - API key
   * @param {Object} options - Generation options
   * @returns {Promise<Object>} Generated blog post
   */
  async generateBlog(apiKey, options) {
    return await this.generateContent(apiKey, {
      ...options,
      action: 'blog',
    })
  },

  /**
   * Generate content outline
   * @param {string} apiKey - API key
   * @param {Object} options - Generation options
   * @returns {Promise<Object>} Generated outline
   */
  async generateOutline(apiKey, options) {
    return await this.generateContent(apiKey, {
      ...options,
      action: 'outline',
    })
  },

  /**
   * Summarize text
   * @param {string} apiKey - API key
   * @param {string} text - Text to summarize
   * @returns {Promise<Object>} Summary
   */
  async summarize(apiKey, text) {
    return await this.generateContent(apiKey, {
      topic: text,
      action: 'summary',
      length: 'short',
    })
  },

  /**
   * Expand text into article
   * @param {string} apiKey - API key
   * @param {string} text - Text to expand
   * @param {Object} options - Additional options
   * @returns {Promise<Object>} Expanded content
   */
  async expand(apiKey, text, options = {}) {
    return await this.generateContent(apiKey, {
      topic: text,
      action: 'expand',
      ...options,
    })
  },

  /**
   * Get usage statistics
   * @param {string} apiKey - API key
   * @returns {Promise<Object>} Usage stats
   */
  async getUsage(apiKey) {
    return await this.request('/extension/usage', {
      method: 'GET',
    }, apiKey)
  },

  /**
   * Check API health
   * @returns {Promise<Object>} Health status
   */
  async healthCheck() {
    return await this.request('/health', {
      method: 'GET',
    })
  },
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
  module.exports = BlogAI
}
