'use client'

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  ClipboardDocumentIcon,
  ArrowDownTrayIcon,
  ArrowUturnLeftIcon,
  EyeIcon,
  PencilSquareIcon,
  CheckIcon,
} from '@heroicons/react/24/outline'
import EditorToolbar, { type FormatAction } from './editor/EditorToolbar'
import {
  markdownToHtml,
  countWords,
  estimateReadingTime,
  applyBold,
  applyItalic,
  applyHeading2,
  applyHeading3,
  applyBulletList,
  applyNumberedList,
  applyLink,
  applyCodeBlock,
  type TextSelection,
  type FormatResult,
} from './editor/markdownUtils'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type EditorMode = 'preview' | 'edit'

interface ContentEditorProps {
  /** The original markdown content produced by the AI generator. */
  initialContent: string
  /** A stable key used for localStorage persistence (e.g. conversation id). */
  storageKey: string
  /** Optional title shown above the editor. */
  title?: string
  /** Callback fired whenever the user's edited content changes. */
  onChange?: (markdown: string) => void
}

interface HistoryEntry {
  text: string
  cursorStart: number
  cursorEnd: number
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const AUTO_SAVE_DELAY_MS = 2000
const MAX_HISTORY_SIZE = 100

// ---------------------------------------------------------------------------
// Helper: localStorage wrappers
// ---------------------------------------------------------------------------

function loadDraft(key: string): string | null {
  try {
    return localStorage.getItem(`content-editor-draft:${key}`)
  } catch {
    return null
  }
}

function saveDraft(key: string, value: string): void {
  try {
    localStorage.setItem(`content-editor-draft:${key}`, value)
  } catch {
    // Storage full or unavailable -- silently ignore
  }
}

function clearDraft(key: string): void {
  try {
    localStorage.removeItem(`content-editor-draft:${key}`)
  } catch {
    // Ignore
  }
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

function useContentEditorView({
  initialContent,
  storageKey,
  title,
  onChange,
}: ContentEditorProps): React.ReactElement {
  // ---- State ---------------------------------------------------------------

  const [mode, setMode] = useState<EditorMode>('preview')
  const [content, setContent] = useState<string>(() => {
    const draft = loadDraft(storageKey)
    return draft ?? initialContent
  })

  // Has the user made any edits since the original content was set?
  const isModified = content !== initialContent

  // Copy-to-clipboard feedback
  const [copied, setCopied] = useState(false)

  // Undo / redo
  const [history, setHistory] = useState<HistoryEntry[]>([
    { text: content, cursorStart: 0, cursorEnd: 0 },
  ])
  const [historyIndex, setHistoryIndex] = useState(0)

  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const previewRef = useRef<HTMLDivElement>(null)
  const autoSaveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // ---- Derived values ------------------------------------------------------

  const wordCount = useMemo(() => countWords(content), [content])
  const readingTime = useMemo(() => estimateReadingTime(wordCount), [wordCount])

  // The markdownToHtml utility escapes all user-provided content through
  // escapeHtml before producing output, so the resulting HTML is safe for
  // rendering. No external or untrusted HTML is ever injected.
  const previewHtml = useMemo(() => markdownToHtml(content), [content])

  // ---- Auto-save -----------------------------------------------------------

  useEffect(() => {
    if (autoSaveTimerRef.current) {
      clearTimeout(autoSaveTimerRef.current)
    }
    autoSaveTimerRef.current = setTimeout(() => {
      saveDraft(storageKey, content)
    }, AUTO_SAVE_DELAY_MS)

    return () => {
      if (autoSaveTimerRef.current) {
        clearTimeout(autoSaveTimerRef.current)
      }
    }
  }, [content, storageKey])

  // ---- History management --------------------------------------------------

  const pushHistory = useCallback(
    (text: string, cursorStart: number, cursorEnd: number) => {
      setHistory((prev) => {
        // Trim any forward history (redo states)
        const base = prev.slice(0, historyIndex + 1)
        const next = [...base, { text, cursorStart, cursorEnd }]
        // Cap size
        if (next.length > MAX_HISTORY_SIZE) {
          next.shift()
          return next
        }
        return next
      })
      setHistoryIndex((prev) => Math.min(prev + 1, MAX_HISTORY_SIZE - 1))
    },
    [historyIndex]
  )

  const canUndo = historyIndex > 0
  const canRedo = historyIndex < history.length - 1

  const undo = useCallback(() => {
    if (!canUndo) return
    const newIndex = historyIndex - 1
    const entry = history[newIndex]
    if (!entry) return
    setHistoryIndex(newIndex)
    setContent(entry.text)
    onChange?.(entry.text)
    requestAnimationFrame(() => {
      const ta = textareaRef.current
      if (ta) {
        ta.selectionStart = entry.cursorStart
        ta.selectionEnd = entry.cursorEnd
      }
    })
  }, [canUndo, history, historyIndex, onChange])

  const redo = useCallback(() => {
    if (!canRedo) return
    const newIndex = historyIndex + 1
    const entry = history[newIndex]
    if (!entry) return
    setHistoryIndex(newIndex)
    setContent(entry.text)
    onChange?.(entry.text)
    requestAnimationFrame(() => {
      const ta = textareaRef.current
      if (ta) {
        ta.selectionStart = entry.cursorStart
        ta.selectionEnd = entry.cursorEnd
      }
    })
  }, [canRedo, history, historyIndex, onChange])

  // ---- Content updates -----------------------------------------------------

  const updateContent = useCallback(
    (newText: string, cursorStart: number, cursorEnd: number) => {
      setContent(newText)
      onChange?.(newText)
      pushHistory(newText, cursorStart, cursorEnd)
    },
    [onChange, pushHistory]
  )

  const handleTextareaChange = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      const newText = e.target.value
      updateContent(newText, e.target.selectionStart, e.target.selectionEnd)
    },
    [updateContent]
  )

  // ---- Formatting actions --------------------------------------------------

  const getSelection = useCallback((): TextSelection => {
    const ta = textareaRef.current
    if (!ta) return { start: 0, end: 0, value: content }
    return {
      start: ta.selectionStart,
      end: ta.selectionEnd,
      value: content,
    }
  }, [content])

  const applyFormat = useCallback(
    (result: FormatResult) => {
      setContent(result.text)
      onChange?.(result.text)
      pushHistory(result.text, result.selectionStart, result.selectionEnd)

      requestAnimationFrame(() => {
        const ta = textareaRef.current
        if (ta) {
          ta.focus()
          ta.selectionStart = result.selectionStart
          ta.selectionEnd = result.selectionEnd
        }
      })
    },
    [onChange, pushHistory]
  )

  const handleToolbarAction = useCallback(
    (action: FormatAction) => {
      if (action === 'undo') {
        undo()
        return
      }
      if (action === 'redo') {
        redo()
        return
      }

      // If in preview mode, switch to edit mode first
      if (mode === 'preview') {
        setMode('edit')
      }

      const sel = getSelection()

      const formatters: Record<
        Exclude<FormatAction, 'undo' | 'redo'>,
        (text: string, sel: TextSelection) => FormatResult
      > = {
        bold: applyBold,
        italic: applyItalic,
        heading2: applyHeading2,
        heading3: applyHeading3,
        bulletList: applyBulletList,
        numberedList: applyNumberedList,
        link: applyLink,
        codeBlock: applyCodeBlock,
      }

      const formatter = formatters[action]
      if (formatter) {
        applyFormat(formatter(content, sel))
      }
    },
    [mode, getSelection, content, applyFormat, undo, redo]
  )

  // ---- Clipboard -----------------------------------------------------------

  const handleCopy = useCallback(async () => {
    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(content)
      } else {
        // Fallback
        const ta = document.createElement('textarea')
        ta.value = content
        ta.style.position = 'fixed'
        ta.style.left = '-9999px'
        document.body.appendChild(ta)
        ta.select()
        document.execCommand('copy')
        document.body.removeChild(ta)
      }
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // Ignore
    }
  }, [content])

  // ---- Export as markdown file ---------------------------------------------

  const handleExportMarkdown = useCallback(() => {
    const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    const sanitizedTitle = (title ?? 'content')
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-|-$/g, '')
      .substring(0, 50)
    link.href = url
    link.download = `${sanitizedTitle || 'content'}.md`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }, [content, title])

  // ---- Revert --------------------------------------------------------------

  const handleRevert = useCallback(() => {
    setContent(initialContent)
    onChange?.(initialContent)
    clearDraft(storageKey)
    setHistory([{ text: initialContent, cursorStart: 0, cursorEnd: 0 }])
    setHistoryIndex(0)
  }, [initialContent, storageKey, onChange])

  const resetEditorState = useCallback((newContent: string) => {
    setContent(newContent)
    setHistory([{ text: newContent, cursorStart: 0, cursorEnd: 0 }])
    setHistoryIndex(0)
  }, [])

  // ---- Auto-resize textarea ------------------------------------------------

  useEffect(() => {
    const ta = textareaRef.current
    if (ta && mode === 'edit') {
      ta.style.height = 'auto'
      ta.style.height = `${ta.scrollHeight}px`
    }
  }, [content, mode])

  // ---- Reset content when initialContent changes (new generation) ----------

  const prevInitialRef = useRef(initialContent)
  useEffect(() => {
    if (initialContent !== prevInitialRef.current) {
      prevInitialRef.current = initialContent
      const draft = loadDraft(storageKey)
      const newContent = draft ?? initialContent
      resetEditorState(newContent)
    }
  }, [initialContent, resetEditorState, storageKey])

  useEffect(() => {
    if (mode !== 'preview') return
    if (!previewRef.current) return
    previewRef.current.innerHTML = previewHtml
  }, [mode, previewHtml])

  // ---- Render --------------------------------------------------------------

  return (
    <div className="flex flex-col gap-4">
      {/* Top bar: mode toggle + metrics + action buttons */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        {/* Mode toggle */}
        <div
          className="inline-flex rounded-lg bg-gray-100 p-0.5"
          role="tablist"
          aria-label="Editor mode"
        >
          <button
            type="button"
            role="tab"
            aria-selected={mode === 'preview'}
            onClick={() => setMode('preview')}
            className={`inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500 ${
              mode === 'preview'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-800'
            }`}
          >
            <EyeIcon className="w-4 h-4" aria-hidden="true" />
            Preview
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={mode === 'edit'}
            onClick={() => setMode('edit')}
            className={`inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500 ${
              mode === 'edit'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-800'
            }`}
          >
            <PencilSquareIcon className="w-4 h-4" aria-hidden="true" />
            Edit
          </button>
        </div>

        {/* Metrics + actions */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Word count / reading time */}
          <span className="text-xs text-gray-500">
            {wordCount.toLocaleString()} {wordCount === 1 ? 'word' : 'words'}
            <span className="mx-1.5 text-gray-300" aria-hidden="true">|</span>
            {readingTime} min read
          </span>

          {/* Copy */}
          <button
            type="button"
            onClick={handleCopy}
            aria-label="Copy to clipboard"
            title="Copy to clipboard"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-700 bg-white border border-gray-200 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-amber-500 transition-colors"
          >
            {copied ? (
              <>
                <CheckIcon className="w-3.5 h-3.5 text-emerald-600" aria-hidden="true" />
                Copied
              </>
            ) : (
              <>
                <ClipboardDocumentIcon className="w-3.5 h-3.5" aria-hidden="true" />
                Copy
              </>
            )}
          </button>

          {/* Export markdown */}
          <button
            type="button"
            onClick={handleExportMarkdown}
            aria-label="Export as Markdown"
            title="Export as Markdown"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-700 bg-white border border-gray-200 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-amber-500 transition-colors"
          >
            <ArrowDownTrayIcon className="w-3.5 h-3.5" aria-hidden="true" />
            Export .md
          </button>

          {/* Revert */}
          {isModified && (
            <button
              type="button"
              onClick={handleRevert}
              aria-label="Revert to original"
              title="Revert to original"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-amber-700 bg-amber-50 border border-amber-200 rounded-md hover:bg-amber-100 focus:outline-none focus:ring-2 focus:ring-amber-500 transition-colors"
            >
              <ArrowUturnLeftIcon className="w-3.5 h-3.5" aria-hidden="true" />
              Revert
            </button>
          )}
        </div>
      </div>

      {/* Toolbar (visible in edit mode) */}
      {mode === 'edit' && (
        <EditorToolbar
          onAction={handleToolbarAction}
          canUndo={canUndo}
          canRedo={canRedo}
        />
      )}

      {/* Content area */}
      <div
        role="tabpanel"
        aria-label={mode === 'edit' ? 'Markdown editor' : 'Content preview'}
        className="min-h-[300px]"
      >
        {mode === 'edit' ? (
          <textarea
            ref={textareaRef}
            value={content}
            onChange={handleTextareaChange}
            className="w-full min-h-[400px] p-4 font-mono text-sm text-gray-800 bg-white border border-gray-200 rounded-lg resize-y focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent leading-relaxed"
            placeholder="Start writing in markdown..."
            aria-label="Content editor"
            spellCheck
          />
        ) : (
          <div
            ref={previewRef}
            className="prose prose-lg max-w-none p-4 bg-white border border-gray-200 rounded-lg min-h-[400px]"
          />
        )}
      </div>

      {/* Auto-save indicator */}
      {isModified && (
        <p className="text-xs text-gray-400 text-right" aria-live="polite">
          Draft auto-saved
        </p>
      )}
    </div>
  )
}

export default function ContentEditor(
  props: ContentEditorProps
): React.ReactElement {
  return useContentEditorView(props)
}
