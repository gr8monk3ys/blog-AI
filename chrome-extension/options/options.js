/**
 * Blog AI Chrome Extension - Options Page Script
 *
 * Handles settings management including:
 * - API key configuration
 * - Default generation settings
 * - Theme preferences
 * - Data management
 */

// DOM Elements
const elements = {
  // Status
  statusMessage: document.getElementById('status-message'),
  statusText: document.getElementById('status-text'),

  // Connection
  connectionIndicator: document.getElementById('connection-indicator'),
  connectionValue: document.getElementById('connection-value'),
  apiKeyInput: document.getElementById('api-key'),
  toggleVisibility: document.getElementById('toggle-visibility'),
  saveApiKeyBtn: document.getElementById('save-api-key'),

  // Settings
  defaultTone: document.getElementById('default-tone'),
  defaultLength: document.getElementById('default-length'),
  includeResearch: document.getElementById('include-research'),
  enableProofreading: document.getElementById('enable-proofreading'),

  // Advanced
  apiEndpoint: document.getElementById('api-endpoint'),
  theme: document.getElementById('theme'),

  // Actions
  saveSettingsBtn: document.getElementById('save-settings'),
  resetSettingsBtn: document.getElementById('reset-settings'),
  clearDataBtn: document.getElementById('clear-data'),
}

// Default settings
const DEFAULT_SETTINGS = {
  defaultTone: 'professional',
  defaultLength: 'medium',
  includeResearch: false,
  enableProofreading: true,
  apiEndpoint: 'https://api.blogai.com',
  theme: 'system',
}

/**
 * Initialize options page
 */
async function init() {
  // Load current settings
  await loadSettings()

  // Check connection status
  await checkConnection()

  // Setup event listeners
  setupEventListeners()

  // Apply theme
  applyTheme()
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
  // API key visibility toggle
  elements.toggleVisibility.addEventListener('click', toggleApiKeyVisibility)

  // Save API key
  elements.saveApiKeyBtn.addEventListener('click', saveApiKey)

  // Enter key on API input
  elements.apiKeyInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      saveApiKey()
    }
  })

  // Save settings
  elements.saveSettingsBtn.addEventListener('click', saveSettings)

  // Reset settings
  elements.resetSettingsBtn.addEventListener('click', resetSettings)

  // Clear data
  elements.clearDataBtn.addEventListener('click', clearAllData)

  // Theme change - apply immediately
  elements.theme.addEventListener('change', () => {
    applyTheme(elements.theme.value)
  })
}

/**
 * Load settings from storage
 */
async function loadSettings() {
  try {
    // Load API key from local storage
    const { apiKey } = await chrome.storage.local.get(['apiKey'])
    if (apiKey) {
      elements.apiKeyInput.value = apiKey
    }

    // Load settings from sync storage
    const { settings } = await chrome.storage.sync.get(['settings'])
    const currentSettings = { ...DEFAULT_SETTINGS, ...settings }

    // Apply settings to form
    elements.defaultTone.value = currentSettings.defaultTone
    elements.defaultLength.value = currentSettings.defaultLength
    elements.includeResearch.checked = currentSettings.includeResearch
    elements.enableProofreading.checked = currentSettings.enableProofreading
    elements.apiEndpoint.value = currentSettings.apiEndpoint
    elements.theme.value = currentSettings.theme
  } catch (error) {
    console.error('Failed to load settings:', error)
    showStatus('Failed to load settings', 'error')
  }
}

/**
 * Check API connection status
 */
async function checkConnection() {
  try {
    const { apiKey } = await chrome.storage.local.get(['apiKey'])

    if (!apiKey) {
      updateConnectionStatus(false, 'Not connected')
      return
    }

    // Get the API endpoint
    const { settings } = await chrome.storage.sync.get(['settings'])
    const endpoint = settings?.apiEndpoint || DEFAULT_SETTINGS.apiEndpoint

    // Verify API key
    const response = await fetch(`${endpoint}/extension/auth`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ api_key: apiKey }),
    })

    if (response.ok) {
      const data = await response.json()
      updateConnectionStatus(true, `Connected as ${data.email || 'User'}`)
    } else {
      updateConnectionStatus(false, 'Invalid API key')
    }
  } catch (error) {
    console.error('Connection check failed:', error)
    updateConnectionStatus(false, 'Connection failed')
  }
}

/**
 * Update connection status display
 * @param {boolean} connected - Whether connected
 * @param {string} message - Status message
 */
function updateConnectionStatus(connected, message) {
  elements.connectionIndicator.className = `connection-indicator ${connected ? 'connected' : 'disconnected'}`
  elements.connectionValue.textContent = message
}

/**
 * Toggle API key visibility
 */
function toggleApiKeyVisibility() {
  const input = elements.apiKeyInput
  const isPassword = input.type === 'password'

  input.type = isPassword ? 'text' : 'password'
  elements.toggleVisibility.textContent = isPassword ? 'Hide' : 'Show'
}

/**
 * Save API key
 */
async function saveApiKey() {
  const apiKey = elements.apiKeyInput.value.trim()

  if (!apiKey) {
    showStatus('Please enter an API key', 'error')
    return
  }

  elements.saveApiKeyBtn.disabled = true
  elements.saveApiKeyBtn.textContent = 'Saving...'

  try {
    // Get the API endpoint
    const { settings } = await chrome.storage.sync.get(['settings'])
    const endpoint = settings?.apiEndpoint || DEFAULT_SETTINGS.apiEndpoint

    // Verify the API key first
    const response = await fetch(`${endpoint}/extension/auth`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ api_key: apiKey }),
    })

    if (response.ok) {
      // Save to storage
      await chrome.storage.local.set({ apiKey })

      const data = await response.json()
      updateConnectionStatus(true, `Connected as ${data.email || 'User'}`)
      showStatus('API key saved successfully!', 'success')
    } else {
      const error = await response.json()
      showStatus(error.detail || 'Invalid API key', 'error')
    }
  } catch (error) {
    console.error('Failed to save API key:', error)
    showStatus('Failed to verify API key. Please check your connection.', 'error')
  } finally {
    elements.saveApiKeyBtn.disabled = false
    elements.saveApiKeyBtn.textContent = 'Save API Key'
  }
}

/**
 * Save all settings
 */
async function saveSettings() {
  elements.saveSettingsBtn.disabled = true
  elements.saveSettingsBtn.textContent = 'Saving...'

  try {
    const settings = {
      defaultTone: elements.defaultTone.value,
      defaultLength: elements.defaultLength.value,
      includeResearch: elements.includeResearch.checked,
      enableProofreading: elements.enableProofreading.checked,
      apiEndpoint: elements.apiEndpoint.value.trim() || DEFAULT_SETTINGS.apiEndpoint,
      theme: elements.theme.value,
    }

    // Validate API endpoint
    try {
      new URL(settings.apiEndpoint)
    } catch {
      showStatus('Invalid API endpoint URL', 'error')
      elements.saveSettingsBtn.disabled = false
      elements.saveSettingsBtn.textContent = 'Save Settings'
      return
    }

    await chrome.storage.sync.set({ settings })

    // Re-check connection if endpoint changed
    await checkConnection()

    showStatus('Settings saved successfully!', 'success')
  } catch (error) {
    console.error('Failed to save settings:', error)
    showStatus('Failed to save settings', 'error')
  } finally {
    elements.saveSettingsBtn.disabled = false
    elements.saveSettingsBtn.textContent = 'Save Settings'
  }
}

/**
 * Reset settings to defaults
 */
async function resetSettings() {
  if (!confirm('Are you sure you want to reset all settings to defaults? This will not remove your API key.')) {
    return
  }

  try {
    await chrome.storage.sync.set({ settings: DEFAULT_SETTINGS })

    // Reload settings into form
    elements.defaultTone.value = DEFAULT_SETTINGS.defaultTone
    elements.defaultLength.value = DEFAULT_SETTINGS.defaultLength
    elements.includeResearch.checked = DEFAULT_SETTINGS.includeResearch
    elements.enableProofreading.checked = DEFAULT_SETTINGS.enableProofreading
    elements.apiEndpoint.value = DEFAULT_SETTINGS.apiEndpoint
    elements.theme.value = DEFAULT_SETTINGS.theme

    // Apply theme
    applyTheme(DEFAULT_SETTINGS.theme)

    showStatus('Settings reset to defaults', 'success')
  } catch (error) {
    console.error('Failed to reset settings:', error)
    showStatus('Failed to reset settings', 'error')
  }
}

/**
 * Clear all extension data
 */
async function clearAllData() {
  if (!confirm('Are you sure you want to clear all data? This will remove your API key, settings, and generation history. This cannot be undone.')) {
    return
  }

  try {
    // Clear all storage
    await chrome.storage.local.clear()
    await chrome.storage.sync.clear()

    // Reset form
    elements.apiKeyInput.value = ''
    elements.defaultTone.value = DEFAULT_SETTINGS.defaultTone
    elements.defaultLength.value = DEFAULT_SETTINGS.defaultLength
    elements.includeResearch.checked = DEFAULT_SETTINGS.includeResearch
    elements.enableProofreading.checked = DEFAULT_SETTINGS.enableProofreading
    elements.apiEndpoint.value = DEFAULT_SETTINGS.apiEndpoint
    elements.theme.value = DEFAULT_SETTINGS.theme

    // Update connection status
    updateConnectionStatus(false, 'Not connected')

    // Apply theme
    applyTheme(DEFAULT_SETTINGS.theme)

    showStatus('All data cleared successfully', 'success')
  } catch (error) {
    console.error('Failed to clear data:', error)
    showStatus('Failed to clear data', 'error')
  }
}

/**
 * Apply theme
 * @param {string} theme - Theme to apply ('system', 'light', 'dark')
 */
function applyTheme(theme) {
  const themeValue = theme || elements.theme.value

  if (themeValue === 'system') {
    document.documentElement.removeAttribute('data-theme')
  } else {
    document.documentElement.setAttribute('data-theme', themeValue)
  }
}

/**
 * Show status message
 * @param {string} message - Message to show
 * @param {string} type - 'success' or 'error'
 */
function showStatus(message, type) {
  elements.statusText.textContent = message
  elements.statusMessage.className = `status ${type}`

  // Auto-hide after 5 seconds
  setTimeout(() => {
    elements.statusMessage.classList.add('hidden')
  }, 5000)
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', init)
