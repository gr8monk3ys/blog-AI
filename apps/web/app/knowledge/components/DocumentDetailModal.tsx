'use client'

import { Fragment, useCallback, useEffect, useState } from 'react'
import { Dialog, Transition } from '@headlessui/react'
import {
  DocumentTextIcon,
  TrashIcon,
  XMarkIcon,
  ChevronDownIcon,
  ChevronUpIcon,
} from '@heroicons/react/24/outline'
import { apiFetch, API_ENDPOINTS } from '../../../lib/api'
import type { KBDocument, KBChunk, KBChunksResponse } from '../../../types/knowledge'
import { FILE_TYPE_CONFIG, formatBytes } from '../../../types/knowledge'

interface DocumentDetailModalProps {
  document: KBDocument | null
  isOpen: boolean
  onClose: () => void
  onDelete: (docId: string, filename: string) => void
  matchedChunkIds?: Set<string>
  chunkScores?: Map<string, number>
}

export default function DocumentDetailModal({
  document,
  isOpen,
  onClose,
  onDelete,
  matchedChunkIds,
  chunkScores,
}: DocumentDetailModalProps) {
  const [chunks, setChunks] = useState<KBChunk[]>([])
  const [totalChunks, setTotalChunks] = useState(0)
  const [loadingChunks, setLoadingChunks] = useState(false)
  const [expandedChunks, setExpandedChunks] = useState<Set<number>>(new Set())
  const [offset, setOffset] = useState(0)
  const limit = 20

  const fetchChunks = useCallback(
    async (newOffset: number) => {
      if (!document) return
      setLoadingChunks(true)
      try {
        const data = await apiFetch<KBChunksResponse>(
          `${API_ENDPOINTS.knowledge.chunks(document.id)}?limit=${limit}&offset=${newOffset}`
        )
        if (newOffset === 0) {
          setChunks(data.chunks)
        } else {
          setChunks((prev) => [...prev, ...data.chunks])
        }
        setTotalChunks(data.total)
      } catch {
        // If chunks endpoint fails, show empty
        setChunks([])
        setTotalChunks(0)
      } finally {
        setLoadingChunks(false)
      }
    },
    [document]
  )

  useEffect(() => {
    if (isOpen && document) {
      setChunks([])
      setOffset(0)
      setExpandedChunks(new Set())
      fetchChunks(0)
    }
  }, [isOpen, document, fetchChunks])

  const loadMore = () => {
    const newOffset = offset + limit
    setOffset(newOffset)
    fetchChunks(newOffset)
  }

  const toggleExpand = (chunkIndex: number) => {
    setExpandedChunks((prev) => {
      const next = new Set(prev)
      if (next.has(chunkIndex)) next.delete(chunkIndex)
      else next.add(chunkIndex)
      return next
    })
  }

  if (!document) return null

  const ext = document.file_type.toLowerCase()
  const typeConfig = FILE_TYPE_CONFIG[ext]
  const hasMore = chunks.length < totalChunks

  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black/25 backdrop-blur-sm" aria-hidden="true" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel className="w-full max-w-3xl transform overflow-hidden rounded-2xl bg-white dark:bg-gray-900 text-left align-middle shadow-xl transition-all">
                {/* Header */}
                <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3 min-w-0">
                      <DocumentTextIcon
                        className={`h-6 w-6 flex-shrink-0 ${typeConfig?.color || 'text-gray-400'}`}
                      />
                      <div className="min-w-0">
                        <Dialog.Title className="text-lg font-semibold text-gray-900 dark:text-gray-100 truncate">
                          {document.title || document.filename}
                        </Dialog.Title>
                        <div className="flex items-center gap-2 mt-1 flex-wrap">
                          <span
                            className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                              typeConfig
                                ? `bg-gray-100 dark:bg-gray-800 ${typeConfig.color}`
                                : 'bg-gray-100 dark:bg-gray-800 text-gray-500'
                            }`}
                          >
                            {typeConfig?.label || ext.toUpperCase()}
                          </span>
                          <span
                            className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                              document.status === 'ready'
                                ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                                : document.status === 'processing'
                                  ? 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400'
                                  : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
                            }`}
                          >
                            {document.status}
                          </span>
                          <span className="text-xs text-gray-400">
                            {formatBytes(document.file_size_bytes)}
                          </span>
                          <span className="text-xs text-gray-400">
                            {document.chunk_count} chunks
                          </span>
                          <span className="text-xs text-gray-400">
                            {new Date(document.created_at).toLocaleDateString()}
                          </span>
                        </div>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={onClose}
                      className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                    >
                      <XMarkIcon className="h-5 w-5" />
                    </button>
                  </div>
                </div>

                {/* Chunks list */}
                <div className="px-6 py-4 max-h-[60vh] overflow-y-auto">
                  <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                    Chunks ({totalChunks})
                  </h3>
                  {loadingChunks && chunks.length === 0 ? (
                    <div className="py-8 text-center text-sm text-gray-400">
                      Loading chunks...
                    </div>
                  ) : chunks.length === 0 ? (
                    <div className="py-8 text-center text-sm text-gray-400">
                      No chunks available.
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {chunks.map((chunk) => {
                        const isMatched = matchedChunkIds?.has(chunk.id)
                        const score = chunkScores?.get(chunk.id)
                        const isExpanded = expandedChunks.has(chunk.chunk_index)
                        const preview =
                          chunk.content.length > 300 && !isExpanded
                            ? chunk.content.slice(0, 300) + '...'
                            : chunk.content

                        return (
                          <div
                            key={chunk.id}
                            className={`rounded-lg border p-3 ${
                              isMatched
                                ? 'border-l-4 border-l-amber-500 border-amber-200 dark:border-amber-800 bg-amber-50/50 dark:bg-amber-950/20'
                                : 'border-gray-200 dark:border-gray-700'
                            }`}
                          >
                            <div className="flex items-center justify-between mb-1">
                              <div className="flex items-center gap-2">
                                <span className="inline-flex items-center justify-center w-6 h-6 rounded bg-gray-100 dark:bg-gray-800 text-xs font-medium text-gray-600 dark:text-gray-400">
                                  #{chunk.chunk_index + 1}
                                </span>
                                {chunk.page_number != null && (
                                  <span className="text-xs text-gray-400">
                                    p.{chunk.page_number}
                                  </span>
                                )}
                                {chunk.section_title && (
                                  <span className="text-xs text-gray-500 dark:text-gray-400 truncate max-w-[200px]">
                                    {chunk.section_title}
                                  </span>
                                )}
                                <span className="text-xs text-gray-400">
                                  {chunk.token_count} tokens
                                </span>
                              </div>
                              {isMatched && score != null && (
                                <span className="text-xs font-medium text-amber-600 dark:text-amber-400">
                                  Score: {score.toFixed(2)}
                                </span>
                              )}
                            </div>
                            <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap break-words">
                              {preview}
                            </p>
                            {chunk.content.length > 300 && (
                              <button
                                type="button"
                                onClick={() => toggleExpand(chunk.chunk_index)}
                                className="mt-1 text-xs text-amber-600 hover:text-amber-700 flex items-center gap-0.5"
                              >
                                {isExpanded ? (
                                  <>
                                    Show less <ChevronUpIcon className="h-3 w-3" />
                                  </>
                                ) : (
                                  <>
                                    Show more <ChevronDownIcon className="h-3 w-3" />
                                  </>
                                )}
                              </button>
                            )}
                          </div>
                        )
                      })}

                      {hasMore && (
                        <button
                          type="button"
                          onClick={loadMore}
                          disabled={loadingChunks}
                          className="w-full py-2 text-sm text-amber-600 hover:text-amber-700 font-medium disabled:opacity-50"
                        >
                          {loadingChunks ? 'Loading...' : `Load more (${chunks.length}/${totalChunks})`}
                        </button>
                      )}
                    </div>
                  )}
                </div>

                {/* Footer */}
                <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex justify-between">
                  <button
                    type="button"
                    onClick={() => onDelete(document.id, document.filename)}
                    className="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-950/30 rounded-lg transition-colors"
                  >
                    <TrashIcon className="h-4 w-4" />
                    Delete
                  </button>
                  <button
                    type="button"
                    onClick={onClose}
                    className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                  >
                    Close
                  </button>
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  )
}
