'use client'

import { useCallback, useRef, useState } from 'react'
import {
  ArrowUpTrayIcon,
  DocumentTextIcon,
  XMarkIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
} from '@heroicons/react/24/outline'
import { m, AnimatePresence } from 'framer-motion'
import { API_ENDPOINTS, getDefaultHeaders } from '../../../lib/api'
import type { KBTierLimits } from '../../../types/knowledge'
import { FILE_TYPE_CONFIG, formatBytes } from '../../../types/knowledge'

type FileStatus = 'queued' | 'uploading' | 'done' | 'error'

interface QueuedFile {
  file: File
  status: FileStatus
  progress: number
  error?: string
  xhr?: XMLHttpRequest
}

const ALLOWED_EXTENSIONS = new Set(['.pdf', '.docx', '.doc', '.txt', '.md', '.markdown'])
const MAX_FILE_SIZE = 10 * 1024 * 1024 // 10MB

function getExtension(filename: string): string {
  const dot = filename.lastIndexOf('.')
  return dot >= 0 ? filename.slice(dot).toLowerCase() : ''
}

function validateFile(file: File): string | null {
  const ext = getExtension(file.name)
  if (!ALLOWED_EXTENSIONS.has(ext)) {
    return `Unsupported file type: ${ext}`
  }
  if (file.size > MAX_FILE_SIZE) {
    return `File too large (${formatBytes(file.size)}). Max 10MB.`
  }
  return null
}

interface UploadDropZoneProps {
  onUploadComplete: () => void
  tierLimits?: KBTierLimits | null
  showToast: (opts: { message: string; variant: 'success' | 'error' | 'warning' }) => void
}

export default function UploadDropZone({
  onUploadComplete,
  tierLimits,
  showToast,
}: UploadDropZoneProps) {
  const [isDragOver, setIsDragOver] = useState(false)
  const [queue, setQueue] = useState<QueuedFile[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const atDocLimit =
    tierLimits != null &&
    tierLimits.max_documents != null &&
    tierLimits.current_documents >= tierLimits.max_documents

  const nearDocLimit =
    tierLimits != null &&
    tierLimits.max_documents != null &&
    !atDocLimit &&
    tierLimits.current_documents / tierLimits.max_documents > 0.8

  const addFiles = useCallback(
    (files: FileList | File[]) => {
      if (atDocLimit) {
        showToast({
          message: 'Document limit reached. Upgrade your plan to upload more.',
          variant: 'error',
        })
        return
      }

      const newQueued: QueuedFile[] = []
      for (const file of Array.from(files)) {
        const err = validateFile(file)
        if (err) {
          newQueued.push({ file, status: 'error', progress: 0, error: err })
        } else {
          newQueued.push({ file, status: 'queued', progress: 0 })
        }
      }
      setQueue((prev) => [...prev, ...newQueued])
    },
    [atDocLimit, showToast]
  )

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(false)
  }, [])

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      e.stopPropagation()
      setIsDragOver(false)
      if (e.dataTransfer.files.length > 0) {
        addFiles(e.dataTransfer.files)
      }
    },
    [addFiles]
  )

  const handleFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files && e.target.files.length > 0) {
        addFiles(e.target.files)
      }
      e.target.value = ''
    },
    [addFiles]
  )

  const removeFromQueue = useCallback((index: number) => {
    setQueue((prev) => {
      const item = prev[index]
      if (item?.xhr && item.status === 'uploading') {
        item.xhr.abort()
      }
      return prev.filter((_, i) => i !== index)
    })
  }, [])

  const uploadFile = useCallback(
    (queuedFile: QueuedFile, index: number): Promise<void> => {
      return new Promise((resolve) => {
        const xhr = new XMLHttpRequest()
        queuedFile.xhr = xhr

        setQueue((prev) =>
          prev.map((item, i) =>
            i === index ? { ...item, status: 'uploading' as const, progress: 0, xhr } : item
          )
        )

        xhr.upload.onprogress = (e) => {
          if (e.lengthComputable) {
            const pct = Math.round((e.loaded / e.total) * 100)
            setQueue((prev) =>
              prev.map((item, i) => (i === index ? { ...item, progress: pct } : item))
            )
          }
        }

        xhr.onload = () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            setQueue((prev) =>
              prev.map((item, i) =>
                i === index ? { ...item, status: 'done' as const, progress: 100 } : item
              )
            )
          } else {
            let errMsg = 'Upload failed'
            try {
              const body = JSON.parse(xhr.responseText)
              const detail = body?.detail
              if (typeof detail === 'string') errMsg = detail
              else if (detail?.error) errMsg = detail.error
            } catch {
              // ignore parse error
            }
            setQueue((prev) =>
              prev.map((item, i) =>
                i === index ? { ...item, status: 'error' as const, error: errMsg } : item
              )
            )
          }
          resolve()
        }

        xhr.onerror = () => {
          setQueue((prev) =>
            prev.map((item, i) =>
              i === index
                ? { ...item, status: 'error' as const, error: 'Network error' }
                : item
            )
          )
          resolve()
        }

        xhr.onabort = () => {
          setQueue((prev) =>
            prev.map((item, i) =>
              i === index
                ? { ...item, status: 'error' as const, error: 'Cancelled' }
                : item
            )
          )
          resolve()
        }

        const formData = new FormData()
        formData.append('file', queuedFile.file)

        // We need to get auth headers, but XHR doesn't support async open
        // So we get headers first, then send
        getDefaultHeaders().then((headers) => {
          xhr.open('POST', API_ENDPOINTS.knowledge.upload)
          // Set auth headers (skip Content-Type — browser sets multipart boundary)
          for (const [key, value] of Object.entries(headers)) {
            if (key !== 'Content-Type') {
              xhr.setRequestHeader(key, value as string)
            }
          }
          xhr.send(formData)
        })
      })
    },
    []
  )

  const startUpload = useCallback(async () => {
    setIsUploading(true)
    const pendingIndices = queue
      .map((item, i) => (item.status === 'queued' ? i : -1))
      .filter((i) => i >= 0)

    let successCount = 0
    for (const idx of pendingIndices) {
      // Re-read queue to get current item (may have been cancelled)
      const current = queue[idx]
      if (!current || current.status !== 'queued') continue
      await uploadFile(current, idx)
      // Check if it succeeded
      setQueue((prev) => {
        if (prev[idx]?.status === 'done') successCount++
        return prev
      })
    }

    setIsUploading(false)
    if (successCount > 0) {
      onUploadComplete()
      showToast({
        message: `${successCount} file${successCount > 1 ? 's' : ''} uploaded successfully`,
        variant: 'success',
      })
    }
  }, [queue, uploadFile, onUploadComplete, showToast])

  const hasPending = queue.some((f) => f.status === 'queued')

  const statusIcon = (status: FileStatus) => {
    switch (status) {
      case 'done':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />
      case 'error':
        return <ExclamationCircleIcon className="h-5 w-5 text-red-500" />
      default:
        return null
    }
  }

  return (
    <div className="space-y-3">
      {/* Quota warnings */}
      {atDocLimit && (
        <div className="px-4 py-3 rounded-lg bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 text-sm text-red-700 dark:text-red-400">
          Document limit reached. <a href="/pricing" className="underline font-medium">Upgrade your plan</a> to upload more.
        </div>
      )}
      {nearDocLimit && (
        <div className="px-4 py-3 rounded-lg bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 text-sm text-amber-700 dark:text-amber-400">
          Approaching document limit ({tierLimits!.current_documents}/{tierLimits!.max_documents}).
        </div>
      )}

      {/* Drop zone */}
      <m.div
        onDragOver={handleDragOver}
        onDragEnter={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !atDocLimit && inputRef.current?.click()}
        animate={isDragOver ? { scale: 1.01 } : { scale: 1 }}
        className={`flex flex-col items-center justify-center w-full h-32 border-2 border-dashed rounded-lg transition-colors ${
          atDocLimit
            ? 'border-gray-300 dark:border-gray-700 bg-gray-100 dark:bg-gray-800/30 cursor-not-allowed opacity-60'
            : isDragOver
              ? 'border-amber-500 bg-amber-50 dark:bg-amber-950/20 cursor-copy'
              : 'border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-800/50 hover:bg-gray-100 dark:hover:bg-gray-800 cursor-pointer'
        }`}
      >
        <ArrowUpTrayIcon className={`h-8 w-8 mb-2 ${isDragOver ? 'text-amber-500' : 'text-gray-400'}`} />
        <p className="text-sm text-gray-500 dark:text-gray-400">
          {atDocLimit ? (
            'Upload disabled — document limit reached'
          ) : isDragOver ? (
            <span className="text-amber-600 font-semibold">Drop files here</span>
          ) : (
            <>
              <span className="font-semibold">Click to upload</span> or drag and drop
            </>
          )}
        </p>
        <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
          PDF, DOCX, TXT, or MD (max 10MB)
        </p>
        <input
          ref={inputRef}
          type="file"
          className="hidden"
          accept=".pdf,.docx,.doc,.txt,.md,.markdown"
          multiple
          onChange={handleFileInput}
          disabled={atDocLimit}
        />
      </m.div>

      {/* File queue */}
      <AnimatePresence>
        {queue.length > 0 && (
          <m.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="space-y-2"
          >
            {queue.map((item, idx) => {
              const ext = getExtension(item.file.name).replace('.', '')
              const typeConfig = FILE_TYPE_CONFIG[ext]
              return (
                <m.div
                  key={`${item.file.name}-${idx}`}
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  className="flex items-center gap-3 px-3 py-2 rounded-lg bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700"
                >
                  <DocumentTextIcon
                    className={`h-5 w-5 flex-shrink-0 ${typeConfig?.color || 'text-gray-400'}`}
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <p className="text-sm text-gray-900 dark:text-gray-100 truncate">
                        {item.file.name}
                      </p>
                      <span className="text-xs text-gray-400 ml-2 flex-shrink-0">
                        {formatBytes(item.file.size)}
                      </span>
                    </div>
                    {/* Progress bar */}
                    {item.status === 'uploading' && (
                      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5 mt-1">
                        <m.div
                          initial={{ width: 0 }}
                          animate={{ width: `${item.progress}%` }}
                          className="h-1.5 rounded-full bg-amber-500"
                        />
                      </div>
                    )}
                    {item.status === 'error' && item.error && (
                      <p className="text-xs text-red-500 mt-0.5">{item.error}</p>
                    )}
                  </div>
                  {/* Status / remove */}
                  <div className="flex-shrink-0 flex items-center gap-1">
                    {statusIcon(item.status)}
                    {item.status === 'uploading' && (
                      <span className="text-xs text-amber-600 font-medium">{item.progress}%</span>
                    )}
                    {item.status === 'queued' && (
                      <span className="text-xs text-gray-400">Queued</span>
                    )}
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation()
                        removeFromQueue(idx)
                      }}
                      className="text-gray-400 hover:text-red-500 transition-colors p-0.5"
                      aria-label={`Remove ${item.file.name}`}
                    >
                      <XMarkIcon className="h-4 w-4" />
                    </button>
                  </div>
                </m.div>
              )
            })}

            {/* Upload button */}
            {hasPending && (
              <button
                type="button"
                onClick={startUpload}
                disabled={isUploading}
                className="w-full px-4 py-2 text-sm font-medium text-white bg-amber-600 rounded-lg hover:bg-amber-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isUploading ? 'Uploading...' : `Upload ${queue.filter((f) => f.status === 'queued').length} file(s)`}
              </button>
            )}
          </m.div>
        )}
      </AnimatePresence>
    </div>
  )
}
