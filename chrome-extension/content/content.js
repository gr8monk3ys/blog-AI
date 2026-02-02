/**
 * Blog AI Chrome Extension - Content Script
 *
 * Injected into web pages to:
 * - Detect text selection
 * - Show floating action button on selection
 * - Display generation results
 * - Highlight selected text for context
 */

// Namespace to avoid conflicts with page scripts
const BlogAIContent = {
  /**
   * State
   */
  state: {
    selectedText: '',
    fabElement: null,
    resultModal: null,
    isInitialized: false,
  },

  /**
   * Initialize content script
   */
  init() {
    if (this.state.isInitialized) return
    this.state.isInitialized = true

    // Setup event listeners
    this.setupSelectionListener()
    this.setupMessageListener()

    console.log('[Blog AI] Content script initialized')
  },

  /**
   * Setup text selection listener
   */
  setupSelectionListener() {
    // Track mouse up to detect selection end
    document.addEventListener('mouseup', (e) => {
      // Small delay to allow selection to complete
      setTimeout(() => this.handleSelection(e), 10)
    })

    // Track keyboard selection (Shift + Arrow keys)
    document.addEventListener('keyup', (e) => {
      if (e.shiftKey) {
        setTimeout(() => this.handleSelection(e), 10)
      }
    })

    // Remove FAB when clicking elsewhere
    document.addEventListener('mousedown', (e) => {
      if (this.state.fabElement && !this.state.fabElement.contains(e.target)) {
        this.hideFab()
      }
    })

    // Handle scroll - reposition or hide FAB
    document.addEventListener('scroll', () => {
      if (this.state.fabElement) {
        this.hideFab()
      }
    }, { passive: true })
  },

  /**
   * Setup message listener for communication with background script
   */
  setupMessageListener() {
    chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
      switch (message.action) {
        case 'getSelection':
          sendResponse({ selection: this.getSelectedText() })
          break

        case 'showResult':
          this.showResult(message.data, message.type)
          sendResponse({ success: true })
          break

        case 'highlight':
          this.highlightSelection()
          sendResponse({ success: true })
          break

        default:
          console.log('[Blog AI] Unknown message:', message.action)
      }
      return true
    })
  },

  /**
   * Handle text selection
   * @param {Event} e - Mouse or keyboard event
   */
  handleSelection(e) {
    const selection = window.getSelection()
    const selectedText = selection.toString().trim()

    // Hide FAB if no selection
    if (!selectedText || selectedText.length < 5) {
      this.hideFab()
      this.state.selectedText = ''
      return
    }

    // Don't show FAB if selection is too long (likely accidental)
    if (selectedText.length > 5000) {
      return
    }

    // Don't show if selection is in an input/textarea
    const anchorNode = selection.anchorNode
    if (anchorNode) {
      const parentElement = anchorNode.parentElement
      if (parentElement) {
        const tagName = parentElement.tagName.toLowerCase()
        if (tagName === 'input' || tagName === 'textarea') {
          return
        }
      }
    }

    this.state.selectedText = selectedText

    // Get selection position
    const range = selection.getRangeAt(0)
    const rect = range.getBoundingClientRect()

    // Show FAB near selection
    this.showFab(rect)
  },

  /**
   * Get currently selected text
   * @returns {string} Selected text
   */
  getSelectedText() {
    return window.getSelection().toString().trim() || this.state.selectedText
  },

  /**
   * Show floating action button
   * @param {DOMRect} rect - Selection bounding rectangle
   */
  showFab(rect) {
    // Remove existing FAB
    this.hideFab()

    // Create FAB element
    const fab = document.createElement('div')
    fab.id = 'blogai-fab'
    fab.setAttribute('role', 'button')
    fab.setAttribute('aria-label', 'Generate with Blog AI')
    fab.setAttribute('tabindex', '0')

    fab.innerHTML = `
      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="M12 20h9"></path>
        <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path>
      </svg>
      <span>Generate</span>
    `

    // Position FAB
    const top = rect.bottom + window.scrollY + 8
    const left = rect.left + window.scrollX + (rect.width / 2) - 50

    fab.style.cssText = `
      top: ${top}px;
      left: ${Math.max(10, left)}px;
    `

    // Add click handler
    fab.addEventListener('click', () => this.handleFabClick())
    fab.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault()
        this.handleFabClick()
      }
    })

    document.body.appendChild(fab)
    this.state.fabElement = fab

    // Animate in
    requestAnimationFrame(() => {
      fab.classList.add('visible')
    })
  },

  /**
   * Hide floating action button
   */
  hideFab() {
    if (this.state.fabElement) {
      this.state.fabElement.remove()
      this.state.fabElement = null
    }
  },

  /**
   * Handle FAB click
   */
  async handleFabClick() {
    const text = this.state.selectedText || this.getSelectedText()

    if (!text) {
      console.log('[Blog AI] No text selected')
      return
    }

    this.hideFab()

    // Show quick menu
    this.showQuickMenu(text)
  },

  /**
   * Show quick action menu
   * @param {string} text - Selected text
   */
  showQuickMenu(text) {
    // Remove existing menu
    const existingMenu = document.getElementById('blogai-quick-menu')
    if (existingMenu) {
      existingMenu.remove()
    }

    const menu = document.createElement('div')
    menu.id = 'blogai-quick-menu'
    menu.setAttribute('role', 'menu')
    menu.setAttribute('aria-label', 'Blog AI generation options')

    const actions = [
      { id: 'blog', label: 'Generate Blog Post', icon: 'file-text' },
      { id: 'outline', label: 'Create Outline', icon: 'list' },
      { id: 'summary', label: 'Summarize', icon: 'align-left' },
      { id: 'expand', label: 'Expand into Article', icon: 'maximize-2' },
    ]

    menu.innerHTML = `
      <div class="blogai-menu-header">
        <strong>Generate with Blog AI</strong>
        <button class="blogai-menu-close" aria-label="Close menu">&times;</button>
      </div>
      <div class="blogai-menu-preview">
        "${this.truncateText(text, 100)}"
      </div>
      <div class="blogai-menu-actions" role="group">
        ${actions.map(action => `
          <button
            class="blogai-menu-action"
            data-action="${action.id}"
            role="menuitem"
          >
            ${this.getIcon(action.icon)}
            <span>${action.label}</span>
          </button>
        `).join('')}
      </div>
    `

    // Position menu in center of viewport
    document.body.appendChild(menu)

    // Add event listeners
    menu.querySelector('.blogai-menu-close').addEventListener('click', () => {
      menu.remove()
    })

    menu.querySelectorAll('.blogai-menu-action').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const action = e.currentTarget.dataset.action
        this.triggerGeneration(text, action)
        menu.remove()
      })
    })

    // Close on click outside
    const closeHandler = (e) => {
      if (!menu.contains(e.target)) {
        menu.remove()
        document.removeEventListener('click', closeHandler)
      }
    }
    setTimeout(() => {
      document.addEventListener('click', closeHandler)
    }, 100)

    // Close on escape
    const escHandler = (e) => {
      if (e.key === 'Escape') {
        menu.remove()
        document.removeEventListener('keydown', escHandler)
      }
    }
    document.addEventListener('keydown', escHandler)

    // Animate in
    requestAnimationFrame(() => {
      menu.classList.add('visible')
    })
  },

  /**
   * Trigger content generation
   * @param {string} text - Text to generate from
   * @param {string} action - Action type
   */
  async triggerGeneration(text, action) {
    // Show loading indicator
    this.showLoading(`Generating ${action}...`)

    try {
      // Send message to background script
      chrome.runtime.sendMessage({
        action: 'generate',
        options: {
          topic: text,
          action: action,
        },
      }, (response) => {
        this.hideLoading()

        if (chrome.runtime.lastError) {
          this.showError('Failed to connect to Blog AI')
          return
        }

        if (response && response.success) {
          this.showResult(response.data, action)
        } else {
          this.showError(response?.error || 'Generation failed')
        }
      })
    } catch (error) {
      this.hideLoading()
      this.showError(error.message || 'Generation failed')
    }
  },

  /**
   * Show loading indicator
   * @param {string} message - Loading message
   */
  showLoading(message) {
    const existing = document.getElementById('blogai-loading')
    if (existing) existing.remove()

    const loader = document.createElement('div')
    loader.id = 'blogai-loading'
    loader.setAttribute('role', 'alert')
    loader.setAttribute('aria-live', 'polite')

    loader.innerHTML = `
      <div class="blogai-loading-spinner"></div>
      <span>${message}</span>
    `

    document.body.appendChild(loader)

    requestAnimationFrame(() => {
      loader.classList.add('visible')
    })
  },

  /**
   * Hide loading indicator
   */
  hideLoading() {
    const loader = document.getElementById('blogai-loading')
    if (loader) {
      loader.classList.remove('visible')
      setTimeout(() => loader.remove(), 200)
    }
  },

  /**
   * Show error message
   * @param {string} message - Error message
   */
  showError(message) {
    const existing = document.getElementById('blogai-error')
    if (existing) existing.remove()

    const error = document.createElement('div')
    error.id = 'blogai-error'
    error.setAttribute('role', 'alert')

    error.innerHTML = `
      <span>${this.escapeHtml(message)}</span>
      <button aria-label="Close">&times;</button>
    `

    error.querySelector('button').addEventListener('click', () => {
      error.remove()
    })

    document.body.appendChild(error)

    requestAnimationFrame(() => {
      error.classList.add('visible')
    })

    // Auto-hide after 5 seconds
    setTimeout(() => {
      if (error.parentNode) {
        error.classList.remove('visible')
        setTimeout(() => error.remove(), 200)
      }
    }, 5000)
  },

  /**
   * Show generation result
   * @param {Object} data - Generated content
   * @param {string} type - Content type
   */
  showResult(data, type) {
    // Remove existing modal
    const existing = document.getElementById('blogai-result-modal')
    if (existing) existing.remove()

    const modal = document.createElement('div')
    modal.id = 'blogai-result-modal'
    modal.setAttribute('role', 'dialog')
    modal.setAttribute('aria-labelledby', 'blogai-result-title')
    modal.setAttribute('aria-modal', 'true')

    const title = data.title || 'Generated Content'
    const content = this.formatContent(data)

    modal.innerHTML = `
      <div class="blogai-modal-backdrop"></div>
      <div class="blogai-modal-content" role="document">
        <div class="blogai-modal-header">
          <h2 id="blogai-result-title">${this.escapeHtml(title)}</h2>
          <button class="blogai-modal-close" aria-label="Close modal">&times;</button>
        </div>
        <div class="blogai-modal-body">
          ${content}
        </div>
        <div class="blogai-modal-footer">
          <button class="blogai-btn blogai-btn-secondary" data-action="copy">
            Copy to Clipboard
          </button>
          <button class="blogai-btn blogai-btn-primary" data-action="open">
            Open in New Tab
          </button>
        </div>
      </div>
    `

    document.body.appendChild(modal)

    // Focus management
    const closeBtn = modal.querySelector('.blogai-modal-close')
    closeBtn.focus()

    // Event listeners
    modal.querySelector('.blogai-modal-backdrop').addEventListener('click', () => {
      this.closeResultModal()
    })

    closeBtn.addEventListener('click', () => {
      this.closeResultModal()
    })

    modal.querySelector('[data-action="copy"]').addEventListener('click', () => {
      this.copyToClipboard(this.formatContentForCopy(data))
    })

    modal.querySelector('[data-action="open"]').addEventListener('click', () => {
      chrome.runtime.sendMessage({
        action: 'openResult',
        data: data,
      })
      this.closeResultModal()
    })

    // Escape to close
    const escHandler = (e) => {
      if (e.key === 'Escape') {
        this.closeResultModal()
        document.removeEventListener('keydown', escHandler)
      }
    }
    document.addEventListener('keydown', escHandler)

    // Prevent body scroll
    document.body.style.overflow = 'hidden'

    // Animate in
    requestAnimationFrame(() => {
      modal.classList.add('visible')
    })

    this.state.resultModal = modal
  },

  /**
   * Close result modal
   */
  closeResultModal() {
    const modal = this.state.resultModal || document.getElementById('blogai-result-modal')
    if (modal) {
      modal.classList.remove('visible')
      setTimeout(() => modal.remove(), 200)
      document.body.style.overflow = ''
      this.state.resultModal = null
    }
  },

  /**
   * Format content for display
   * @param {Object} data - Content data
   * @returns {string} HTML string
   */
  formatContent(data) {
    let html = ''

    if (data.description) {
      html += `<p class="blogai-description">${this.escapeHtml(data.description)}</p>`
    }

    if (data.sections) {
      data.sections.forEach(section => {
        html += `<h3>${this.escapeHtml(section.title)}</h3>`
        if (section.subtopics) {
          section.subtopics.forEach(subtopic => {
            if (subtopic.title) {
              html += `<h4>${this.escapeHtml(subtopic.title)}</h4>`
            }
            html += `<p>${this.escapeHtml(subtopic.content)}</p>`
          })
        }
      })
    }

    if (data.content) {
      html += `<p>${this.escapeHtml(data.content)}</p>`
    }

    return html || '<p>No content generated</p>'
  },

  /**
   * Format content for copying
   * @param {Object} data - Content data
   * @returns {string} Plain text
   */
  formatContentForCopy(data) {
    let text = `# ${data.title || 'Generated Content'}\n\n`

    if (data.description) {
      text += `${data.description}\n\n`
    }

    if (data.sections) {
      data.sections.forEach(section => {
        text += `## ${section.title}\n\n`
        if (section.subtopics) {
          section.subtopics.forEach(subtopic => {
            if (subtopic.title) {
              text += `### ${subtopic.title}\n\n`
            }
            text += `${subtopic.content}\n\n`
          })
        }
      })
    }

    if (data.content) {
      text += data.content
    }

    return text.trim()
  },

  /**
   * Copy text to clipboard
   * @param {string} text - Text to copy
   */
  async copyToClipboard(text) {
    try {
      await navigator.clipboard.writeText(text)
      this.showSuccess('Copied to clipboard!')
    } catch (error) {
      this.showError('Failed to copy to clipboard')
    }
  },

  /**
   * Show success message
   * @param {string} message - Success message
   */
  showSuccess(message) {
    const existing = document.getElementById('blogai-success')
    if (existing) existing.remove()

    const success = document.createElement('div')
    success.id = 'blogai-success'
    success.setAttribute('role', 'alert')

    success.innerHTML = `<span>${this.escapeHtml(message)}</span>`

    document.body.appendChild(success)

    requestAnimationFrame(() => {
      success.classList.add('visible')
    })

    setTimeout(() => {
      success.classList.remove('visible')
      setTimeout(() => success.remove(), 200)
    }, 2000)
  },

  /**
   * Highlight current selection
   */
  highlightSelection() {
    const selection = window.getSelection()
    if (!selection.rangeCount) return

    const range = selection.getRangeAt(0)
    const highlight = document.createElement('span')
    highlight.className = 'blogai-highlight'
    highlight.appendChild(range.extractContents())
    range.insertNode(highlight)
  },

  /**
   * Get SVG icon
   * @param {string} name - Icon name
   * @returns {string} SVG HTML
   */
  getIcon(name) {
    const icons = {
      'file-text': '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>',
      'list': '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="8" y1="6" x2="21" y2="6"></line><line x1="8" y1="12" x2="21" y2="12"></line><line x1="8" y1="18" x2="21" y2="18"></line><line x1="3" y1="6" x2="3.01" y2="6"></line><line x1="3" y1="12" x2="3.01" y2="12"></line><line x1="3" y1="18" x2="3.01" y2="18"></line></svg>',
      'align-left': '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="17" y1="10" x2="3" y2="10"></line><line x1="21" y1="6" x2="3" y2="6"></line><line x1="21" y1="14" x2="3" y2="14"></line><line x1="17" y1="18" x2="3" y2="18"></line></svg>',
      'maximize-2': '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 3 21 3 21 9"></polyline><polyline points="9 21 3 21 3 15"></polyline><line x1="21" y1="3" x2="14" y2="10"></line><line x1="3" y1="21" x2="10" y2="14"></line></svg>',
    }
    return icons[name] || ''
  },

  /**
   * Truncate text with ellipsis
   * @param {string} text - Text to truncate
   * @param {number} maxLength - Maximum length
   * @returns {string} Truncated text
   */
  truncateText(text, maxLength) {
    if (text.length <= maxLength) return text
    return text.substring(0, maxLength).trim() + '...'
  },

  /**
   * Escape HTML entities
   * @param {string} str - String to escape
   * @returns {string} Escaped string
   */
  escapeHtml(str) {
    if (!str) return ''
    const div = document.createElement('div')
    div.textContent = str
    return div.innerHTML
  },
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => BlogAIContent.init())
} else {
  BlogAIContent.init()
}
