import { useCallback, useEffect } from 'react'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type FormatAction =
  | 'bold'
  | 'italic'
  | 'heading2'
  | 'heading3'
  | 'bulletList'
  | 'numberedList'
  | 'link'
  | 'codeBlock'
  | 'undo'
  | 'redo'

interface ToolbarButton {
  action: FormatAction
  label: string
  icon: React.ReactNode
  shortcutDisplay?: string
}

interface EditorToolbarProps {
  onAction: (action: FormatAction) => void
  canUndo: boolean
  canRedo: boolean
  disabled?: boolean
}

// ---------------------------------------------------------------------------
// Icon components (inline SVG to avoid extra dependencies)
// ---------------------------------------------------------------------------

function BoldIcon(): React.ReactElement {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2.5}
      strokeLinecap="round"
      strokeLinejoin="round"
      className="w-4 h-4"
      aria-hidden="true"
    >
      <path d="M6 4h8a4 4 0 0 1 4 4 4 4 0 0 1-4 4H6z" />
      <path d="M6 12h9a4 4 0 0 1 4 4 4 4 0 0 1-4 4H6z" />
    </svg>
  )
}

function ItalicIcon(): React.ReactElement {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      className="w-4 h-4"
      aria-hidden="true"
    >
      <line x1="19" y1="4" x2="10" y2="4" />
      <line x1="14" y1="20" x2="5" y2="20" />
      <line x1="15" y1="4" x2="9" y2="20" />
    </svg>
  )
}

function Heading2Icon(): React.ReactElement {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      className="w-4 h-4"
      aria-hidden="true"
    >
      <path d="M4 12h8" />
      <path d="M4 18V6" />
      <path d="M12 18V6" />
      <path d="M21 18h-4c0-4 4-3 4-6 0-1.5-2-2.5-4-1" />
    </svg>
  )
}

function Heading3Icon(): React.ReactElement {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      className="w-4 h-4"
      aria-hidden="true"
    >
      <path d="M4 12h8" />
      <path d="M4 18V6" />
      <path d="M12 18V6" />
      <path d="M17.5 10.5c1.7-1 3.5 0 3.5 1.5a2 2 0 0 1-2 2" />
      <path d="M17 17.5c2 1.5 4 .3 4-1.5a2 2 0 0 0-2-2" />
    </svg>
  )
}

function BulletListIcon(): React.ReactElement {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      className="w-4 h-4"
      aria-hidden="true"
    >
      <line x1="8" y1="6" x2="21" y2="6" />
      <line x1="8" y1="12" x2="21" y2="12" />
      <line x1="8" y1="18" x2="21" y2="18" />
      <circle cx="4" cy="6" r="1" fill="currentColor" />
      <circle cx="4" cy="12" r="1" fill="currentColor" />
      <circle cx="4" cy="18" r="1" fill="currentColor" />
    </svg>
  )
}

function NumberedListIcon(): React.ReactElement {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      className="w-4 h-4"
      aria-hidden="true"
    >
      <line x1="10" y1="6" x2="21" y2="6" />
      <line x1="10" y1="12" x2="21" y2="12" />
      <line x1="10" y1="18" x2="21" y2="18" />
      <text x="2" y="8" fontSize="8" fill="currentColor" fontFamily="sans-serif">1</text>
      <text x="2" y="14" fontSize="8" fill="currentColor" fontFamily="sans-serif">2</text>
      <text x="2" y="20" fontSize="8" fill="currentColor" fontFamily="sans-serif">3</text>
    </svg>
  )
}

function LinkIcon(): React.ReactElement {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      className="w-4 h-4"
      aria-hidden="true"
    >
      <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
      <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
    </svg>
  )
}

function CodeBlockIcon(): React.ReactElement {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      className="w-4 h-4"
      aria-hidden="true"
    >
      <polyline points="16 18 22 12 16 6" />
      <polyline points="8 6 2 12 8 18" />
    </svg>
  )
}

function UndoIcon(): React.ReactElement {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      className="w-4 h-4"
      aria-hidden="true"
    >
      <path d="M3 7v6h6" />
      <path d="M21 17a9 9 0 0 0-9-9 9 9 0 0 0-6 2.3L3 13" />
    </svg>
  )
}

function RedoIcon(): React.ReactElement {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      className="w-4 h-4"
      aria-hidden="true"
    >
      <path d="M21 7v6h-6" />
      <path d="M3 17a9 9 0 0 1 9-9 9 9 0 0 1 6 2.3L21 13" />
    </svg>
  )
}

// ---------------------------------------------------------------------------
// Button definitions
// ---------------------------------------------------------------------------

const FORMATTING_BUTTONS: ToolbarButton[] = [
  { action: 'bold', label: 'Bold', icon: <BoldIcon />, shortcutDisplay: 'Ctrl+B' },
  { action: 'italic', label: 'Italic', icon: <ItalicIcon />, shortcutDisplay: 'Ctrl+I' },
  { action: 'heading2', label: 'Heading 2', icon: <Heading2Icon />, shortcutDisplay: 'Ctrl+2' },
  { action: 'heading3', label: 'Heading 3', icon: <Heading3Icon />, shortcutDisplay: 'Ctrl+3' },
  { action: 'bulletList', label: 'Bullet list', icon: <BulletListIcon />, shortcutDisplay: 'Ctrl+U' },
  { action: 'numberedList', label: 'Numbered list', icon: <NumberedListIcon />, shortcutDisplay: 'Ctrl+O' },
  { action: 'link', label: 'Insert link', icon: <LinkIcon />, shortcutDisplay: 'Ctrl+K' },
  { action: 'codeBlock', label: 'Code block', icon: <CodeBlockIcon />, shortcutDisplay: 'Ctrl+E' },
]

const HISTORY_BUTTONS: ToolbarButton[] = [
  { action: 'undo', label: 'Undo', icon: <UndoIcon />, shortcutDisplay: 'Ctrl+Z' },
  { action: 'redo', label: 'Redo', icon: <RedoIcon />, shortcutDisplay: 'Ctrl+Y' },
]

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function EditorToolbar({
  onAction,
  canUndo,
  canRedo,
  disabled = false,
}: EditorToolbarProps): React.ReactElement {
  // Keyboard shortcuts
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (disabled) return

      const mod = e.ctrlKey || e.metaKey
      if (!mod) return

      const key = e.key.toLowerCase()

      if (key === 'b') {
        e.preventDefault()
        onAction('bold')
      } else if (key === 'i') {
        e.preventDefault()
        onAction('italic')
      } else if (key === 'k') {
        e.preventDefault()
        onAction('link')
      } else if (key === 'e') {
        e.preventDefault()
        onAction('codeBlock')
      } else if (key === '2') {
        e.preventDefault()
        onAction('heading2')
      } else if (key === '3') {
        e.preventDefault()
        onAction('heading3')
      } else if (key === 'u' && !e.shiftKey) {
        e.preventDefault()
        onAction('bulletList')
      } else if (key === 'o' && !e.shiftKey) {
        e.preventDefault()
        onAction('numberedList')
      } else if (key === 'z' && !e.shiftKey) {
        e.preventDefault()
        onAction('undo')
      } else if (key === 'y' || (key === 'z' && e.shiftKey)) {
        e.preventDefault()
        onAction('redo')
      }
    },
    [disabled, onAction]
  )

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown)
    return () => {
      document.removeEventListener('keydown', handleKeyDown)
    }
  }, [handleKeyDown])

  const isDisabled = (action: FormatAction): boolean => {
    if (disabled) return true
    if (action === 'undo') return !canUndo
    if (action === 'redo') return !canRedo
    return false
  }

  return (
    <div
      className="flex flex-wrap items-center gap-0.5 px-2 py-1.5 bg-gray-50 border border-gray-200 rounded-lg"
      role="toolbar"
      aria-label="Text formatting"
    >
      {/* Formatting buttons */}
      <div className="flex flex-wrap items-center gap-0.5">
        {FORMATTING_BUTTONS.map((btn) => (
          <button
            key={btn.action}
            type="button"
            onClick={() => onAction(btn.action)}
            disabled={isDisabled(btn.action)}
            aria-label={btn.label}
            title={btn.shortcutDisplay ? `${btn.label} (${btn.shortcutDisplay})` : btn.label}
            className="inline-flex items-center justify-center w-8 h-8 rounded-md text-gray-600 hover:bg-gray-200 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-1 disabled:opacity-40 disabled:pointer-events-none transition-colors"
          >
            {btn.icon}
          </button>
        ))}
      </div>

      {/* Separator */}
      <div className="hidden sm:block w-px h-5 bg-gray-300 mx-1" aria-hidden="true" />

      {/* Undo / Redo */}
      <div className="flex items-center gap-0.5">
        {HISTORY_BUTTONS.map((btn) => (
          <button
            key={btn.action}
            type="button"
            onClick={() => onAction(btn.action)}
            disabled={isDisabled(btn.action)}
            aria-label={btn.label}
            title={btn.shortcutDisplay ? `${btn.label} (${btn.shortcutDisplay})` : btn.label}
            className="inline-flex items-center justify-center w-8 h-8 rounded-md text-gray-600 hover:bg-gray-200 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-1 disabled:opacity-40 disabled:pointer-events-none transition-colors"
          >
            {btn.icon}
          </button>
        ))}
      </div>
    </div>
  )
}
