/**
 * Blog AI Chrome Extension - Popup Script
 *
 * Handles the popup UI interactions including:
 * - API key authentication
 * - Content generation form
 * - Recent generations list
 * - Communication with background service worker
 */

// DOM Elements
const elements = {
  // Status
  connectionStatus: document.getElementById('connection-status'),
  statusText: document.querySelector('.status-text'),

  // Auth
  authSection: document.getElementById('auth-section'),
  apiKeyInput: document.getElementById('api-key-input'),
  toggleKeyVisibility: document.getElementById('toggle-key-visibility'),
  connectBtn: document.getElementById('connect-btn'),

  // Main
  mainSection: document.getElementById('main-section'),
  settingsBtn: document.getElementById('settings-btn'),

  // Form
  generateForm: document.getElementById('generate-form'),
  topicInput: document.getElementById('topic-input'),
  toneSelect: document.getElementById('tone-select'),
  lengthSelect: document.getElementById('length-select'),
  providerSelect: document.getElementById('provider-select'),
  keywordsInput: document.getElementById('keywords-input'),
  researchCheckbox: document.getElementById('research-checkbox'),
  proofreadCheckbox: document.getElementById('proofread-checkbox'),
  useSelectionBtn: document.getElementById('use-selection-btn'),
  generateBtn: document.getElementById('generate-btn'),

  // Progress
  progressSection: document.getElementById('progress-section'),
  progressText: document.getElementById('progress-text'),

  // Recent
  recentList: document.getElementById('recent-list'),
  noRecent: document.getElementById('no-recent'),

  // Toast
  toast: document.getElementById('toast'),
  toastMessage: document.getElementById('toast-message'),
  toastClose: document.getElementById('toast-close'),
}

// State
let isConnected = false
let isGenerating = false

/**
 * Initialize the popup
 */
async function init() {
  // Check connection status
  await checkConnection()

  // Load saved default settings (tone/length/provider, etc.)
  await loadSettings()

  // Load recent generations
  await loadRecentGenerations()

  // Setup event listeners
  setupEventListeners()

  // Check for selected text
  await checkSelectedText()
}

/**
 * Load saved settings to prefill the popup form.
 */
async function loadSettings() {
  try {
    const { settings } = await chrome.storage.sync.get(['settings'])
    const current = settings || {}

    if (current.defaultTone) elements.toneSelect.value = current.defaultTone
    if (current.defaultLength) elements.lengthSelect.value = current.defaultLength
    if (current.defaultProvider && elements.providerSelect) {
      elements.providerSelect.value = current.defaultProvider
    }
    if (typeof current.includeResearch === 'boolean') {
      elements.researchCheckbox.checked = current.includeResearch
    }
    if (typeof current.enableProofreading === 'boolean') {
      elements.proofreadCheckbox.checked = current.enableProofreading
    }
  } catch (error) {
    console.error('Failed to load settings:', error)
  }
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
  // Settings button
  elements.settingsBtn.addEventListener('click', openOptions)

  // API key visibility toggle
  elements.toggleKeyVisibility.addEventListener('click', toggleApiKeyVisibility)

  // Connect button
  elements.connectBtn.addEventListener('click', handleConnect)

  // API key input - enter to connect
  elements.apiKeyInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      handleConnect()
    }
  })

  // Use selection button
  elements.useSelectionBtn.addEventListener('click', handleUseSelection)

  // Generate form submit
  elements.generateForm.addEventListener('submit', handleGenerate)

  // Toast close
  elements.toastClose.addEventListener('click', hideToast)
}

/**
 * Check API connection status
 */
async function checkConnection() {
  updateConnectionStatus('checking', 'Checking connection...')

  try {
    const result = await chrome.storage.local.get(['apiKey', 'userInfo'])

    if (!result.apiKey) {
      updateConnectionStatus('disconnected', 'Not connected')
      showAuthSection()
      return
    }

    // Verify the API key is still valid
    const response = await BlogAI.verifyApiKey(result.apiKey)

    if (response.success) {
      isConnected = true
      updateConnectionStatus('connected', `Connected as ${response.data.email || 'User'}`)
      showMainSection()

      // Update user info in storage
      await chrome.storage.local.set({ userInfo: response.data })
    } else {
      updateConnectionStatus('disconnected', 'Invalid API key')
      showAuthSection()
    }
  } catch (error) {
    console.error('Connection check failed:', error)
    updateConnectionStatus('disconnected', 'Connection failed')
    showAuthSection()
  }
}

/**
 * Update connection status display
 * @param {string} status - 'checking', 'connected', 'disconnected'
 * @param {string} message - Status message
 */
function updateConnectionStatus(status, message) {
  elements.connectionStatus.className = `status-bar ${status}`
  elements.statusText.textContent = message
}

/**
 * Show authentication section
 */
function showAuthSection() {
  elements.authSection.classList.remove('hidden')
  elements.mainSection.classList.add('hidden')
}

/**
 * Show main section
 */
function showMainSection() {
  elements.authSection.classList.add('hidden')
  elements.mainSection.classList.remove('hidden')
}

/**
 * Toggle API key visibility
 */
function toggleApiKeyVisibility() {
  const input = elements.apiKeyInput
  const isPassword = input.type === 'password'

  input.type = isPassword ? 'text' : 'password'
  elements.toggleKeyVisibility.setAttribute(
    'aria-label',
    isPassword ? 'Hide API key' : 'Show API key'
  )
}

/**
 * Handle connect button click
 */
async function handleConnect() {
  const apiKey = elements.apiKeyInput.value.trim()

  if (!apiKey) {
    showToast('Please enter your API key', 'error')
    elements.apiKeyInput.focus()
    return
  }

  elements.connectBtn.disabled = true
  elements.connectBtn.textContent = 'Connecting...'

  try {
    const response = await BlogAI.verifyApiKey(apiKey)

    if (response.success) {
      // Save API key and user info
      await chrome.storage.local.set({
        apiKey: apiKey,
        userInfo: response.data,
      })

      isConnected = true
      updateConnectionStatus('connected', `Connected as ${response.data.email || 'User'}`)
      showMainSection()
      showToast('Connected successfully!', 'success')
    } else {
      showToast(response.error || 'Invalid API key', 'error')
    }
  } catch (error) {
    console.error('Connection failed:', error)
    showToast('Failed to connect. Please try again.', 'error')
  } finally {
    elements.connectBtn.disabled = false
    elements.connectBtn.textContent = 'Connect'
  }
}

/**
 * Handle use selection button click
 */
async function handleUseSelection() {
  try {
    // Get the active tab
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true })

    if (!tab) {
      showToast('No active tab found', 'error')
      return
    }

    // Request selected text from content script
    chrome.tabs.sendMessage(tab.id, { action: 'getSelection' }, (response) => {
      if (chrome.runtime.lastError) {
        showToast('Cannot access this page. Try refreshing.', 'error')
        return
      }

      if (response && response.selection) {
        elements.topicInput.value = response.selection
        showToast('Text selection added', 'success')
      } else {
        showToast('No text selected on the page', 'error')
      }
    })
  } catch (error) {
    console.error('Failed to get selection:', error)
    showToast('Failed to get selection', 'error')
  }
}

/**
 * Check for selected text when popup opens
 */
async function checkSelectedText() {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true })

    if (!tab || !tab.url || tab.url.startsWith('chrome://')) {
      return
    }

    chrome.tabs.sendMessage(tab.id, { action: 'getSelection' }, (response) => {
      if (!chrome.runtime.lastError && response && response.selection) {
        elements.topicInput.value = response.selection
        elements.topicInput.focus()
      }
    })
  } catch (error) {
    // Silently ignore - content script may not be loaded
  }
}

/**
 * Handle generate form submission
 * @param {Event} e - Form submit event
 */
async function handleGenerate(e) {
  e.preventDefault()

  if (isGenerating) return

  const topic = elements.topicInput.value.trim()

  if (!topic) {
    showToast('Please enter a topic or select text', 'error')
    elements.topicInput.focus()
    return
  }

  const keywords = elements.keywordsInput.value
    .split(',')
    .map((k) => k.trim())
    .filter(Boolean)

  const options = {
    topic: topic,
    tone: elements.toneSelect.value,
    length: elements.lengthSelect.value,
    providerType: elements.providerSelect?.value || 'openai',
    keywords: keywords,
    research: elements.researchCheckbox.checked,
    proofread: elements.proofreadCheckbox.checked,
  }

  isGenerating = true
  showProgress('Generating content...')

  try {
    // Get API key
    const { apiKey } = await chrome.storage.local.get(['apiKey'])

    if (!apiKey) {
      throw new Error('API key not found. Please reconnect.')
    }

    const response = await BlogAI.generateContent(apiKey, options)

    if (response.success) {
      // Save to recent generations
      await saveRecentGeneration({
        id: Date.now(),
        title: response.data.title || topic.substring(0, 50),
        topic: topic,
        tone: options.tone,
        createdAt: new Date().toISOString(),
        content: response.data,
      })

      // Reload recent list
      await loadRecentGenerations()

      // Clear form
      elements.topicInput.value = ''
      elements.keywordsInput.value = ''

      showToast('Content generated successfully!', 'success')

      // Open result in new tab or send to content script
      chrome.runtime.sendMessage({
        action: 'openResult',
        data: response.data,
      })
    } else {
      showToast(response.error || 'Generation failed', 'error')
    }
  } catch (error) {
    console.error('Generation failed:', error)
    showToast(error.message || 'Generation failed. Please try again.', 'error')
  } finally {
    isGenerating = false
    hideProgress()
  }
}

/**
 * Show progress indicator
 * @param {string} message - Progress message
 */
function showProgress(message) {
  elements.progressSection.classList.remove('hidden')
  elements.progressText.textContent = message
  elements.generateBtn.disabled = true
  elements.useSelectionBtn.disabled = true
}

/**
 * Hide progress indicator
 */
function hideProgress() {
  elements.progressSection.classList.add('hidden')
  elements.generateBtn.disabled = false
  elements.useSelectionBtn.disabled = false
}

/**
 * Load recent generations from storage
 */
async function loadRecentGenerations() {
  try {
    const { recentGenerations = [] } = await chrome.storage.local.get(['recentGenerations'])

    elements.recentList.innerHTML = ''

    if (recentGenerations.length === 0) {
      elements.noRecent.classList.remove('hidden')
      return
    }

    elements.noRecent.classList.add('hidden')

    // Show last 5 generations
    const recent = recentGenerations.slice(0, 5)

    recent.forEach((item) => {
      const li = document.createElement('li')
      li.innerHTML = `
        <div class="recent-item-content">
          <div class="recent-item-title">${escapeHtml(item.title)}</div>
          <div class="recent-item-meta">${formatDate(item.createdAt)} - ${item.tone}</div>
        </div>
        <div class="recent-item-actions">
          <button
            class="icon-btn"
            data-action="view"
            data-id="${item.id}"
            aria-label="View content"
            title="View"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
              <circle cx="12" cy="12" r="3"></circle>
            </svg>
          </button>
          <button
            class="icon-btn"
            data-action="copy"
            data-id="${item.id}"
            aria-label="Copy content"
            title="Copy"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
            </svg>
          </button>
        </div>
      `

      // Add event listeners
      li.querySelector('[data-action="view"]').addEventListener('click', () => viewGeneration(item))
      li.querySelector('[data-action="copy"]').addEventListener('click', () => copyGeneration(item))

      elements.recentList.appendChild(li)
    })
  } catch (error) {
    console.error('Failed to load recent generations:', error)
  }
}

/**
 * Save a generation to recent list
 * @param {Object} generation - Generation data
 */
async function saveRecentGeneration(generation) {
  try {
    const { recentGenerations = [] } = await chrome.storage.local.get(['recentGenerations'])

    // Add new generation to the beginning
    recentGenerations.unshift(generation)

    // Keep only last 20 generations
    const trimmed = recentGenerations.slice(0, 20)

    await chrome.storage.local.set({ recentGenerations: trimmed })
  } catch (error) {
    console.error('Failed to save generation:', error)
  }
}

/**
 * View a generation
 * @param {Object} item - Generation item
 */
function viewGeneration(item) {
  chrome.runtime.sendMessage({
    action: 'openResult',
    data: item.content,
  })
}

/**
 * Copy generation content to clipboard
 * @param {Object} item - Generation item
 */
async function copyGeneration(item) {
  try {
    const content = formatContentForCopy(item.content)
    await navigator.clipboard.writeText(content)
    showToast('Content copied to clipboard', 'success')
  } catch (error) {
    console.error('Failed to copy:', error)
    showToast('Failed to copy content', 'error')
  }
}

/**
 * Format content for copying
 * @param {Object} content - Content object
 * @returns {string} Formatted text
 */
function formatContentForCopy(content) {
  if (!content) return ''

  let text = `# ${content.title || 'Untitled'}\n\n`

  if (content.description) {
    text += `${content.description}\n\n`
  }

  if (content.sections) {
    content.sections.forEach((section) => {
      text += `## ${section.title}\n\n`
      if (section.subtopics) {
        section.subtopics.forEach((subtopic) => {
          if (subtopic.title) {
            text += `### ${subtopic.title}\n\n`
          }
          text += `${subtopic.content}\n\n`
        })
      }
    })
  }

  return text.trim()
}

/**
 * Open options page
 */
function openOptions() {
  chrome.runtime.openOptionsPage()
}

/**
 * Show toast notification
 * @param {string} message - Toast message
 * @param {string} type - 'success', 'error', or default
 */
function showToast(message, type = '') {
  elements.toastMessage.textContent = message
  elements.toast.className = `toast ${type}`

  // Auto-hide after 4 seconds
  setTimeout(hideToast, 4000)
}

/**
 * Hide toast notification
 */
function hideToast() {
  elements.toast.classList.add('hidden')
}

/**
 * Escape HTML to prevent XSS
 * @param {string} str - String to escape
 * @returns {string} Escaped string
 */
function escapeHtml(str) {
  const div = document.createElement('div')
  div.textContent = str
  return div.innerHTML
}

/**
 * Format date for display
 * @param {string} isoString - ISO date string
 * @returns {string} Formatted date
 */
function formatDate(isoString) {
  const date = new Date(isoString)
  const now = new Date()
  const diffMs = now - date
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`

  return date.toLocaleDateString()
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', init)
