/**
 * Blog AI Chrome Extension - Background Service Worker
 *
 * Handles:
 * - Context menu creation and handling
 * - Message routing between popup and content scripts
 * - API call orchestration
 * - Notification handling
 * - Extension lifecycle events
 */

// Import API client
importScripts('../lib/api.js')

// Constants
const CONTEXT_MENU_ID = 'blogai-generate'
const NOTIFICATION_ICON = 'icons/icon128.png'

/**
 * Initialize extension on install
 */
chrome.runtime.onInstalled.addListener(async (details) => {
  console.log('[Blog AI] Extension installed:', details.reason)

  // Create context menu
  createContextMenu()

  // Set default settings on fresh install
  if (details.reason === 'install') {
    await setDefaultSettings()
    showWelcomeNotification()
  }

  // Handle update
  if (details.reason === 'update') {
    console.log('[Blog AI] Updated from version:', details.previousVersion)
  }
})

/**
 * Create context menu items
 */
function createContextMenu() {
  // Remove existing menu items first
  chrome.contextMenus.removeAll(() => {
    // Main context menu item
    chrome.contextMenus.create({
      id: CONTEXT_MENU_ID,
      title: 'Generate with Blog AI',
      contexts: ['selection'],
    })

    // Sub-menu items for different content types
    chrome.contextMenus.create({
      id: `${CONTEXT_MENU_ID}-blog`,
      parentId: CONTEXT_MENU_ID,
      title: 'Generate Blog Post',
      contexts: ['selection'],
    })

    chrome.contextMenus.create({
      id: `${CONTEXT_MENU_ID}-outline`,
      parentId: CONTEXT_MENU_ID,
      title: 'Generate Outline',
      contexts: ['selection'],
    })

    chrome.contextMenus.create({
      id: `${CONTEXT_MENU_ID}-summary`,
      parentId: CONTEXT_MENU_ID,
      title: 'Summarize Text',
      contexts: ['selection'],
    })

    chrome.contextMenus.create({
      id: `${CONTEXT_MENU_ID}-expand`,
      parentId: CONTEXT_MENU_ID,
      title: 'Expand into Article',
      contexts: ['selection'],
    })

    console.log('[Blog AI] Context menu created')
  })
}

/**
 * Handle context menu clicks
 */
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  const selectedText = info.selectionText

  if (!selectedText) {
    showNotification('Error', 'No text selected')
    return
  }

  // Determine action based on menu item clicked
  let action = 'blog'
  const menuId = info.menuItemId

  if (menuId.includes('-outline')) {
    action = 'outline'
  } else if (menuId.includes('-summary')) {
    action = 'summary'
  } else if (menuId.includes('-expand')) {
    action = 'expand'
  }

  console.log(`[Blog AI] Context menu action: ${action}`)

  // Check if we have an API key
  const { apiKey } = await chrome.storage.local.get(['apiKey'])

  if (!apiKey) {
    showNotification(
      'API Key Required',
      'Please configure your API key in the extension popup.'
    )
    // Open popup
    chrome.action.openPopup()
    return
  }

  // Show generating notification
  showNotification('Generating...', `Creating ${action} from selected text`)

  try {
    // Get default settings
    const settings = await getSettings()

    // Generate content based on action
    const response = await generateFromSelection(apiKey, selectedText, action, settings)

    if (response.success) {
      // Send result to content script for display
      chrome.tabs.sendMessage(tab.id, {
        action: 'showResult',
        data: response.data,
        type: action,
      })

      showNotification('Success!', `${capitalizeFirst(action)} generated successfully`)

      // Save to recent generations
      await saveRecentGeneration({
        id: Date.now(),
        title: response.data.title || selectedText.substring(0, 50),
        topic: selectedText.substring(0, 100),
        tone: settings.defaultTone || 'professional',
        createdAt: new Date().toISOString(),
        content: response.data,
        type: action,
      })
    } else {
      showNotification('Error', response.error || 'Generation failed')
    }
  } catch (error) {
    console.error('[Blog AI] Generation error:', error)
    showNotification('Error', error.message || 'Generation failed. Please try again.')
  }
})

/**
 * Generate content from selected text
 * @param {string} apiKey - API key
 * @param {string} text - Selected text
 * @param {string} action - Action type
 * @param {Object} settings - User settings
 * @returns {Promise<Object>} Generation result
 */
async function generateFromSelection(apiKey, text, action, settings) {
  const options = {
    topic: text,
    tone: settings.defaultTone || 'professional',
    length: settings.defaultLength || 'medium',
    providerType: settings.defaultProvider || 'openai',
    keywords: [],
    research: settings.includeResearch || false,
    proofread: settings.enableProofreading || true,
    action: action,
  }

  return await BlogAI.generateContent(apiKey, options)
}

/**
 * Handle messages from popup and content scripts
 */
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log('[Blog AI] Received message:', message.action)

  switch (message.action) {
    case 'openResult':
      handleOpenResult(message.data)
      break

    case 'getSelectedText':
      handleGetSelectedText(sender.tab, sendResponse)
      return true // Keep channel open for async response

    case 'checkConnection':
      handleCheckConnection(sendResponse)
      return true

    case 'generate':
      handleGenerate(message.options, sendResponse)
      return true

    default:
      console.log('[Blog AI] Unknown action:', message.action)
  }
})

/**
 * Handle opening result in new tab or modal
 * @param {Object} data - Content data
 */
function handleOpenResult(data) {
  // Create a data URL for the result page
  const resultHtml = createResultHtml(data)
  const dataUrl = `data:text/html;charset=utf-8,${encodeURIComponent(resultHtml)}`

  chrome.tabs.create({ url: dataUrl })
}

/**
 * Create HTML for result display
 * @param {Object} data - Content data
 * @returns {string} HTML string
 */
function createResultHtml(data) {
  const title = data.title || 'Generated Content'
  const description = data.description || ''

  let sectionsHtml = ''
  if (data.sections) {
    data.sections.forEach((section) => {
      sectionsHtml += `<h2>${escapeHtml(section.title)}</h2>`
      if (section.subtopics) {
        section.subtopics.forEach((subtopic) => {
          if (subtopic.title) {
            sectionsHtml += `<h3>${escapeHtml(subtopic.title)}</h3>`
          }
          sectionsHtml += `<p>${escapeHtml(subtopic.content)}</p>`
        })
      }
    })
  }

  return `
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>${escapeHtml(title)} - Blog AI</title>
      <style>
        :root {
          --color-primary: #4F46E5;
          --color-text: #111827;
          --color-text-secondary: #6B7280;
          --color-bg: #FFFFFF;
          --color-border: #E5E7EB;
        }
        @media (prefers-color-scheme: dark) {
          :root {
            --color-primary: #6366F1;
            --color-text: #F9FAFB;
            --color-text-secondary: #D1D5DB;
            --color-bg: #1F2937;
            --color-border: #374151;
          }
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
          line-height: 1.6;
          color: var(--color-text);
          background: var(--color-bg);
          padding: 40px 20px;
          max-width: 800px;
          margin: 0 auto;
        }
        h1 {
          font-size: 2rem;
          margin-bottom: 1rem;
          color: var(--color-primary);
        }
        h2 {
          font-size: 1.5rem;
          margin: 2rem 0 1rem;
          padding-top: 1rem;
          border-top: 1px solid var(--color-border);
        }
        h3 {
          font-size: 1.25rem;
          margin: 1.5rem 0 0.5rem;
        }
        p {
          margin-bottom: 1rem;
          color: var(--color-text-secondary);
        }
        .description {
          font-size: 1.1rem;
          font-style: italic;
          margin-bottom: 2rem;
          padding: 1rem;
          background: var(--color-border);
          border-radius: 8px;
        }
        .actions {
          display: flex;
          gap: 1rem;
          margin-top: 2rem;
          padding-top: 2rem;
          border-top: 1px solid var(--color-border);
        }
        button {
          padding: 10px 20px;
          font-size: 1rem;
          border: none;
          border-radius: 6px;
          cursor: pointer;
          transition: background-color 0.2s;
        }
        .btn-primary {
          background: var(--color-primary);
          color: white;
        }
        .btn-primary:hover {
          opacity: 0.9;
        }
        .btn-secondary {
          background: var(--color-border);
          color: var(--color-text);
        }
        .footer {
          margin-top: 2rem;
          text-align: center;
          color: var(--color-text-secondary);
          font-size: 0.875rem;
        }
        .footer a {
          color: var(--color-primary);
          text-decoration: none;
        }
      </style>
    </head>
    <body>
      <article>
        <h1>${escapeHtml(title)}</h1>
        ${description ? `<p class="description">${escapeHtml(description)}</p>` : ''}
        ${sectionsHtml}
      </article>
      <div class="actions">
        <button class="btn-primary" onclick="copyContent()">Copy to Clipboard</button>
        <button class="btn-secondary" onclick="window.print()">Print/Save as PDF</button>
      </div>
      <div class="footer">
        <p>Generated by <a href="https://blogai.com" target="_blank">Blog AI</a></p>
      </div>
      <script>
        function copyContent() {
          const content = document.querySelector('article').innerText;
          navigator.clipboard.writeText(content)
            .then(() => alert('Content copied to clipboard!'))
            .catch(err => alert('Failed to copy: ' + err));
        }
      </script>
    </body>
    </html>
  `
}

/**
 * Handle get selected text request
 * @param {Object} tab - Chrome tab
 * @param {Function} sendResponse - Response callback
 */
async function handleGetSelectedText(tab, sendResponse) {
  try {
    chrome.tabs.sendMessage(tab.id, { action: 'getSelection' }, (response) => {
      sendResponse(response)
    })
  } catch (error) {
    sendResponse({ error: error.message })
  }
}

/**
 * Handle connection check
 * @param {Function} sendResponse - Response callback
 */
async function handleCheckConnection(sendResponse) {
  try {
    const { apiKey } = await chrome.storage.local.get(['apiKey'])

    if (!apiKey) {
      sendResponse({ connected: false, error: 'No API key configured' })
      return
    }

    const response = await BlogAI.verifyApiKey(apiKey)
    sendResponse({ connected: response.success, user: response.data })
  } catch (error) {
    sendResponse({ connected: false, error: error.message })
  }
}

/**
 * Handle generation request
 * @param {Object} options - Generation options
 * @param {Function} sendResponse - Response callback
 */
async function handleGenerate(options, sendResponse) {
  try {
    const { apiKey } = await chrome.storage.local.get(['apiKey'])

    if (!apiKey) {
      sendResponse({ success: false, error: 'API key not configured' })
      return
    }

    const response = await BlogAI.generateContent(apiKey, options)
    sendResponse(response)
  } catch (error) {
    sendResponse({ success: false, error: error.message })
  }
}

/**
 * Show browser notification
 * @param {string} title - Notification title
 * @param {string} message - Notification message
 */
function showNotification(title, message) {
  chrome.notifications.create({
    type: 'basic',
    iconUrl: NOTIFICATION_ICON,
    title: `Blog AI - ${title}`,
    message: message,
    priority: 1,
  })
}

/**
 * Show welcome notification on first install
 */
function showWelcomeNotification() {
  chrome.notifications.create({
    type: 'basic',
    iconUrl: NOTIFICATION_ICON,
    title: 'Welcome to Blog AI!',
    message: 'Click the extension icon to get started. Enter your API key to begin generating content.',
    priority: 2,
  })
}

/**
 * Set default settings on install
 */
async function setDefaultSettings() {
  const defaultSettings = {
    defaultTone: 'professional',
    defaultLength: 'medium',
    defaultProvider: 'openai',
    includeResearch: false,
    enableProofreading: true,
    theme: 'system',
    apiEndpoint: 'https://api.blogai.com',
  }

  await chrome.storage.sync.set({ settings: defaultSettings })
  console.log('[Blog AI] Default settings initialized')
}

/**
 * Get user settings
 * @returns {Promise<Object>} Settings object
 */
async function getSettings() {
  const { settings } = await chrome.storage.sync.get(['settings'])
  return settings || {}
}

/**
 * Save recent generation
 * @param {Object} generation - Generation data
 */
async function saveRecentGeneration(generation) {
  try {
    const { recentGenerations = [] } = await chrome.storage.local.get(['recentGenerations'])
    recentGenerations.unshift(generation)
    const trimmed = recentGenerations.slice(0, 20)
    await chrome.storage.local.set({ recentGenerations: trimmed })
  } catch (error) {
    console.error('[Blog AI] Failed to save generation:', error)
  }
}

/**
 * Escape HTML entities
 * @param {string} str - String to escape
 * @returns {string} Escaped string
 */
function escapeHtml(str) {
  if (!str) return ''
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
}

/**
 * Capitalize first letter
 * @param {string} str - String to capitalize
 * @returns {string} Capitalized string
 */
function capitalizeFirst(str) {
  return str.charAt(0).toUpperCase() + str.slice(1)
}

// Log service worker startup
console.log('[Blog AI] Service worker started')
