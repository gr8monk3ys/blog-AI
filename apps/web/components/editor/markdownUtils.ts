/**
 * Lightweight markdown utilities for the inline content editor.
 *
 * Converts a subset of markdown to HTML for the live preview pane and
 * provides helpers for inserting formatting tokens into a textarea value.
 */

// ---------------------------------------------------------------------------
// Markdown -> HTML (preview)
// ---------------------------------------------------------------------------

/** Escape HTML entities so user content is never interpreted as raw HTML. */
function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

/**
 * Convert a markdown string into a safe HTML string suitable for
 * `dangerouslySetInnerHTML`. Supports headings, bold, italic, inline code,
 * code blocks, links, images, unordered/ordered lists, blockquotes, and
 * horizontal rules.
 */
export function markdownToHtml(md: string): string {
  const lines = md.split('\n')
  const html: string[] = []
  let inCodeBlock = false
  let codeBlockContent: string[] = []
  let inList: 'ul' | 'ol' | null = null

  const closeList = (): void => {
    if (inList) {
      html.push(inList === 'ul' ? '</ul>' : '</ol>')
      inList = null
    }
  }

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i] ?? ''

    // Fenced code blocks
    if (line.trimStart().startsWith('```')) {
      if (inCodeBlock) {
        html.push(
          `<pre class="bg-gray-100 rounded-lg p-4 overflow-x-auto text-sm"><code>${escapeHtml(
            codeBlockContent.join('\n')
          )}</code></pre>`
        )
        codeBlockContent = []
        inCodeBlock = false
      } else {
        closeList()
        inCodeBlock = true
      }
      continue
    }

    if (inCodeBlock) {
      codeBlockContent.push(line)
      continue
    }

    // Blank line
    if (line.trim() === '') {
      closeList()
      continue
    }

    // Headings
    const headingMatch = /^(#{1,6})\s+(.+)$/.exec(line)
    if (headingMatch) {
      closeList()
      const level = (headingMatch[1] ?? '').length
      const text = inlineFormat(headingMatch[2] ?? '')
      html.push(`<h${level} class="font-semibold mt-6 mb-2">${text}</h${level}>`)
      continue
    }

    // Horizontal rule
    if (/^(-{3,}|_{3,}|\*{3,})$/.test(line.trim())) {
      closeList()
      html.push('<hr class="my-6 border-gray-200" />')
      continue
    }

    // Blockquote
    if (line.trimStart().startsWith('> ')) {
      closeList()
      const text = inlineFormat(line.replace(/^>\s?/, ''))
      html.push(`<blockquote class="border-l-4 border-amber-300 pl-4 italic text-gray-600 my-4">${text}</blockquote>`)
      continue
    }

    // Unordered list
    const ulMatch = /^(\s*)[-*+]\s+(.+)$/.exec(line)
    if (ulMatch) {
      if (inList !== 'ul') {
        closeList()
        html.push('<ul class="list-disc pl-6 my-2 space-y-1">')
        inList = 'ul'
      }
      html.push(`<li>${inlineFormat(ulMatch[2] ?? '')}</li>`)
      continue
    }

    // Ordered list
    const olMatch = /^(\s*)\d+\.\s+(.+)$/.exec(line)
    if (olMatch) {
      if (inList !== 'ol') {
        closeList()
        html.push('<ol class="list-decimal pl-6 my-2 space-y-1">')
        inList = 'ol'
      }
      html.push(`<li>${inlineFormat(olMatch[2] ?? '')}</li>`)
      continue
    }

    // Paragraph
    closeList()
    html.push(`<p class="my-3 leading-relaxed">${inlineFormat(line)}</p>`)
  }

  // Close any open blocks
  if (inCodeBlock && codeBlockContent.length > 0) {
    html.push(
      `<pre class="bg-gray-100 rounded-lg p-4 overflow-x-auto text-sm"><code>${escapeHtml(
        codeBlockContent.join('\n')
      )}</code></pre>`
    )
  }
  closeList()

  return html.join('\n')
}

/** Validate that a URL uses http: or https: protocol; return '#' otherwise. */
function safeUrl(url: string): string {
  try {
    const parsed = new URL(url, 'https://placeholder.invalid')
    if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') return '#'
    return url
  } catch {
    return '#'
  }
}

/** Apply inline formatting (bold, italic, code, links, images). */
function inlineFormat(text: string): string {
  let result = escapeHtml(text)

  // Images: ![alt](url)
  result = result.replace(
    /!\[([^\]]*)\]\(([^)]+)\)/g,
    (_, alt, url) => `<img src="${safeUrl(url)}" alt="${alt}" class="max-w-full rounded my-2" />`
  )

  // Links: [text](url)
  result = result.replace(
    /\[([^\]]+)\]\(([^)]+)\)/g,
    (_, text, url) => `<a href="${safeUrl(url)}" class="text-amber-700 hover:text-amber-800 underline" target="_blank" rel="noreferrer">${text}</a>`
  )

  // Inline code
  result = result.replace(
    /`([^`]+)`/g,
    '<code class="bg-gray-100 px-1.5 py-0.5 rounded text-sm font-mono">$1</code>'
  )

  // Bold + italic
  result = result.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>')

  // Bold
  result = result.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')

  // Italic
  result = result.replace(/\*(.+?)\*/g, '<em>$1</em>')

  return result
}

// ---------------------------------------------------------------------------
// Textarea formatting helpers
// ---------------------------------------------------------------------------

export interface TextSelection {
  start: number
  end: number
  value: string
}

export interface FormatResult {
  text: string
  selectionStart: number
  selectionEnd: number
}

/** Wrap the selection with `before` and `after` tokens. */
function wrapSelection(
  fullText: string,
  selection: TextSelection,
  before: string,
  after: string
): FormatResult {
  const selectedText = fullText.slice(selection.start, selection.end)
  const newText =
    fullText.slice(0, selection.start) +
    before +
    selectedText +
    after +
    fullText.slice(selection.end)

  return {
    text: newText,
    selectionStart: selection.start + before.length,
    selectionEnd: selection.start + before.length + selectedText.length,
  }
}

/** Insert a prefix at the start of the current line. */
function prefixLine(
  fullText: string,
  selection: TextSelection,
  prefix: string
): FormatResult {
  const beforeCursor = fullText.slice(0, selection.start)
  const lineStart = beforeCursor.lastIndexOf('\n') + 1
  const newText =
    fullText.slice(0, lineStart) + prefix + fullText.slice(lineStart)

  return {
    text: newText,
    selectionStart: selection.start + prefix.length,
    selectionEnd: selection.end + prefix.length,
  }
}

export function applyBold(fullText: string, sel: TextSelection): FormatResult {
  return wrapSelection(fullText, sel, '**', '**')
}

export function applyItalic(fullText: string, sel: TextSelection): FormatResult {
  return wrapSelection(fullText, sel, '*', '*')
}

export function applyHeading2(fullText: string, sel: TextSelection): FormatResult {
  return prefixLine(fullText, sel, '## ')
}

export function applyHeading3(fullText: string, sel: TextSelection): FormatResult {
  return prefixLine(fullText, sel, '### ')
}

export function applyBulletList(fullText: string, sel: TextSelection): FormatResult {
  return prefixLine(fullText, sel, '- ')
}

export function applyNumberedList(fullText: string, sel: TextSelection): FormatResult {
  return prefixLine(fullText, sel, '1. ')
}

export function applyLink(fullText: string, sel: TextSelection): FormatResult {
  const selectedText = fullText.slice(sel.start, sel.end)
  const linkText = selectedText || 'link text'
  const replacement = `[${linkText}](url)`
  const newText =
    fullText.slice(0, sel.start) + replacement + fullText.slice(sel.end)

  return {
    text: newText,
    selectionStart: sel.start + 1,
    selectionEnd: sel.start + 1 + linkText.length,
  }
}

export function applyCodeBlock(fullText: string, sel: TextSelection): FormatResult {
  const selectedText = fullText.slice(sel.start, sel.end)
  const before = '\n```\n'
  const after = '\n```\n'
  const replacement = before + selectedText + after
  const newText =
    fullText.slice(0, sel.start) + replacement + fullText.slice(sel.end)

  return {
    text: newText,
    selectionStart: sel.start + before.length,
    selectionEnd: sel.start + before.length + selectedText.length,
  }
}

// ---------------------------------------------------------------------------
// Content metrics
// ---------------------------------------------------------------------------

/** Count words in a string. */
export function countWords(text: string): number {
  const trimmed = text.trim()
  if (trimmed === '') return 0
  return trimmed.split(/\s+/).length
}

/** Estimate reading time in minutes based on average 238 wpm. */
export function estimateReadingTime(wordCount: number): number {
  const WORDS_PER_MINUTE = 238
  return Math.max(1, Math.ceil(wordCount / WORDS_PER_MINUTE))
}
