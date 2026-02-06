'use client'

import { useState, Fragment } from 'react'
import { Menu, Transition } from '@headlessui/react'
import {
  ArrowDownTrayIcon,
  DocumentTextIcon,
  CodeBracketIcon,
  DocumentIcon,
  ClipboardDocumentIcon,
  CheckIcon,
  ChevronDownIcon,
} from '@heroicons/react/24/outline'

export type ExportFormat = 'markdown' | 'html' | 'text' | 'pdf' | 'clipboard' | 'wordpress' | 'medium'

export interface ExportContent {
  title: string
  content: string
  type: 'blog' | 'book' | 'tool'
  metadata?: {
    date?: string
    description?: string
    tags?: string[]
    toolName?: string
  }
}

interface ExportMenuProps {
  content: ExportContent
  onExportStart?: () => void
  onExportComplete?: (format: ExportFormat, success: boolean) => void
  className?: string
  disabled?: boolean
}

interface ExportOption {
  id: ExportFormat
  name: string
  description: string
  icon: React.ElementType
  extension?: string
}

const exportOptions: ExportOption[] = [
  {
    id: 'clipboard',
    name: 'Copy to Clipboard',
    description: 'Copy content as plain text',
    icon: ClipboardDocumentIcon,
  },
  {
    id: 'markdown',
    name: 'Markdown',
    description: 'Download as .md file',
    icon: DocumentTextIcon,
    extension: '.md',
  },
  {
    id: 'html',
    name: 'HTML',
    description: 'Download styled HTML',
    icon: CodeBracketIcon,
    extension: '.html',
  },
  {
    id: 'text',
    name: 'Plain Text',
    description: 'Download as .txt file',
    icon: DocumentIcon,
    extension: '.txt',
  },
  {
    id: 'pdf',
    name: 'PDF',
    description: 'Download as PDF document',
    icon: ArrowDownTrayIcon,
    extension: '.pdf',
  },
]

const publishOptions: ExportOption[] = [
  {
    id: 'wordpress',
    name: 'WordPress',
    description: 'Copy as WordPress block format',
    icon: ClipboardDocumentIcon,
  },
  {
    id: 'medium',
    name: 'Medium',
    description: 'Copy as Medium-compatible HTML',
    icon: ClipboardDocumentIcon,
  },
]

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function ExportMenu({
  content,
  onExportStart,
  onExportComplete,
  className = '',
  disabled = false,
}: ExportMenuProps) {
  const [loading, setLoading] = useState<ExportFormat | null>(null)
  const [copied, setCopied] = useState<ExportFormat | null>(null)

  const getFilename = (extension: string): string => {
    const sanitizedTitle = content.title
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-|-$/g, '')
      .substring(0, 50)
    return `${sanitizedTitle || 'export'}${extension}`
  }

  const downloadFile = (blob: Blob, filename: string) => {
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  const copyToClipboard = async (text: string): Promise<boolean> => {
    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(text)
        return true
      } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea')
        textArea.value = text
        textArea.style.position = 'fixed'
        textArea.style.left = '-9999px'
        textArea.style.top = '-9999px'
        document.body.appendChild(textArea)
        textArea.focus()
        textArea.select()
        const success = document.execCommand('copy')
        document.body.removeChild(textArea)
        return success
      }
    } catch (err) {
      console.error('Failed to copy to clipboard:', err)
      return false
    }
  }

  const handleExport = async (format: ExportFormat) => {
    if (loading || disabled) return

    setLoading(format)
    setCopied(null)
    onExportStart?.()

    try {
      let success = false

      switch (format) {
        case 'clipboard': {
          success = await copyToClipboard(content.content)
          if (success) {
            setCopied(format)
            setTimeout(() => setCopied(null), 2000)
          }
          break
        }

        case 'markdown': {
          const response = await fetch(`${API_BASE_URL}/export/markdown`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              title: content.title,
              content: content.content,
              content_type: content.type,
              metadata: content.metadata,
            }),
          })
          if (response.ok) {
            const blob = await response.blob()
            downloadFile(blob, getFilename('.md'))
            success = true
          }
          break
        }

        case 'html': {
          const response = await fetch(`${API_BASE_URL}/export/html`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              title: content.title,
              content: content.content,
              content_type: content.type,
              metadata: content.metadata,
            }),
          })
          if (response.ok) {
            const blob = await response.blob()
            downloadFile(blob, getFilename('.html'))
            success = true
          }
          break
        }

        case 'text': {
          const response = await fetch(`${API_BASE_URL}/export/text`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              title: content.title,
              content: content.content,
              content_type: content.type,
              metadata: content.metadata,
            }),
          })
          if (response.ok) {
            const blob = await response.blob()
            downloadFile(blob, getFilename('.txt'))
            success = true
          }
          break
        }

        case 'pdf': {
          const response = await fetch(`${API_BASE_URL}/export/pdf`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              title: content.title,
              content: content.content,
              content_type: content.type,
              metadata: content.metadata,
            }),
          })
          if (response.ok) {
            const blob = await response.blob()
            downloadFile(blob, getFilename('.pdf'))
            success = true
          }
          break
        }

        case 'wordpress': {
          const response = await fetch(`${API_BASE_URL}/export/wordpress`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              title: content.title,
              content: content.content,
              content_type: content.type,
              metadata: content.metadata,
            }),
          })
          if (response.ok) {
            const data = await response.json()
            success = await copyToClipboard(data.content)
            if (success) {
              setCopied(format)
              setTimeout(() => setCopied(null), 2000)
            }
          }
          break
        }

        case 'medium': {
          const response = await fetch(`${API_BASE_URL}/export/medium`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              title: content.title,
              content: content.content,
              content_type: content.type,
              metadata: content.metadata,
            }),
          })
          if (response.ok) {
            const data = await response.json()
            success = await copyToClipboard(data.content)
            if (success) {
              setCopied(format)
              setTimeout(() => setCopied(null), 2000)
            }
          }
          break
        }
      }

      onExportComplete?.(format, success)
    } catch (error) {
      console.error(`Export failed for format ${format}:`, error)
      onExportComplete?.(format, false)
    } finally {
      setLoading(null)
    }
  }

  return (
    <Menu as="div" className={`relative inline-block text-left ${className}`}>
      <Menu.Button
        disabled={disabled}
        className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <ArrowDownTrayIcon className="w-4 h-4" aria-hidden="true" />
        Export
        <ChevronDownIcon className="w-4 h-4 ml-1" aria-hidden="true" />
      </Menu.Button>

      <Transition
        as={Fragment}
        enter="transition ease-out duration-100"
        enterFrom="transform opacity-0 scale-95"
        enterTo="transform opacity-100 scale-100"
        leave="transition ease-in duration-75"
        leaveFrom="transform opacity-100 scale-100"
        leaveTo="transform opacity-0 scale-95"
      >
        <Menu.Items className="absolute right-0 z-20 mt-2 w-64 origin-top-right rounded-xl bg-white shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none divide-y divide-gray-100">
          {/* Download options */}
          <div className="p-1">
            <div className="px-3 py-2">
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
                Download
              </p>
            </div>
            {exportOptions.map((option) => (
              <Menu.Item key={option.id}>
                {({ active }) => (
                  <button
                    onClick={() => handleExport(option.id)}
                    disabled={loading !== null}
                    className={`${
                      active ? 'bg-gray-50' : ''
                    } group flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors disabled:opacity-50`}
                  >
                    <span
                      className={`flex-shrink-0 w-8 h-8 rounded-lg ${
                        active ? 'bg-indigo-100' : 'bg-gray-100'
                      } flex items-center justify-center transition-colors`}
                    >
                      {loading === option.id ? (
                        <svg
                          className="animate-spin w-4 h-4 text-indigo-600"
                          xmlns="http://www.w3.org/2000/svg"
                          fill="none"
                          viewBox="0 0 24 24"
                        >
                          <circle
                            className="opacity-25"
                            cx="12"
                            cy="12"
                            r="10"
                            stroke="currentColor"
                            strokeWidth="4"
                          />
                          <path
                            className="opacity-75"
                            fill="currentColor"
                            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                          />
                        </svg>
                      ) : copied === option.id ? (
                        <CheckIcon className="w-4 h-4 text-emerald-600" />
                      ) : (
                        <option.icon
                          className={`w-4 h-4 ${
                            active ? 'text-indigo-600' : 'text-gray-500'
                          } transition-colors`}
                        />
                      )}
                    </span>
                    <span className="flex-1 text-left">
                      <span
                        className={`block font-medium ${
                          active ? 'text-gray-900' : 'text-gray-700'
                        }`}
                      >
                        {copied === option.id ? 'Copied!' : option.name}
                      </span>
                      <span className="block text-xs text-gray-500">
                        {option.description}
                      </span>
                    </span>
                  </button>
                )}
              </Menu.Item>
            ))}
          </div>

          {/* Publishing options */}
          <div className="p-1">
            <div className="px-3 py-2">
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
                Copy for Publishing
              </p>
            </div>
            {publishOptions.map((option) => (
              <Menu.Item key={option.id}>
                {({ active }) => (
                  <button
                    onClick={() => handleExport(option.id)}
                    disabled={loading !== null}
                    className={`${
                      active ? 'bg-gray-50' : ''
                    } group flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors disabled:opacity-50`}
                  >
                    <span
                      className={`flex-shrink-0 w-8 h-8 rounded-lg ${
                        active ? 'bg-indigo-100' : 'bg-gray-100'
                      } flex items-center justify-center transition-colors`}
                    >
                      {loading === option.id ? (
                        <svg
                          className="animate-spin w-4 h-4 text-indigo-600"
                          xmlns="http://www.w3.org/2000/svg"
                          fill="none"
                          viewBox="0 0 24 24"
                        >
                          <circle
                            className="opacity-25"
                            cx="12"
                            cy="12"
                            r="10"
                            stroke="currentColor"
                            strokeWidth="4"
                          />
                          <path
                            className="opacity-75"
                            fill="currentColor"
                            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                          />
                        </svg>
                      ) : copied === option.id ? (
                        <CheckIcon className="w-4 h-4 text-emerald-600" />
                      ) : (
                        <option.icon
                          className={`w-4 h-4 ${
                            active ? 'text-indigo-600' : 'text-gray-500'
                          } transition-colors`}
                        />
                      )}
                    </span>
                    <span className="flex-1 text-left">
                      <span
                        className={`block font-medium ${
                          active ? 'text-gray-900' : 'text-gray-700'
                        }`}
                      >
                        {copied === option.id ? 'Copied!' : option.name}
                      </span>
                      <span className="block text-xs text-gray-500">
                        {option.description}
                      </span>
                    </span>
                  </button>
                )}
              </Menu.Item>
            ))}
          </div>
        </Menu.Items>
      </Transition>
    </Menu>
  )
}
