'use client'

import { useState } from 'react'
import { DocumentTextIcon, TrashIcon } from '@heroicons/react/24/outline'
import type { KBDocument, KBTierLimits } from '../../../types/knowledge'
import { FILE_TYPE_CONFIG, formatBytes } from '../../../types/knowledge'
import UploadDropZone from './UploadDropZone'
import DocumentDetailModal from './DocumentDetailModal'

interface DocumentsTabProps {
  documents: KBDocument[]
  loading: boolean
  tierLimits?: KBTierLimits | null
  onRefresh: () => void
  showToast: (opts: { message: string; variant: 'success' | 'error' | 'warning' }) => void
  confirmDelete: (docId: string, filename: string) => void
}

export default function DocumentsTab({
  documents,
  loading,
  tierLimits,
  onRefresh,
  showToast,
  confirmDelete,
}: DocumentsTabProps) {
  const [selectedDoc, setSelectedDoc] = useState<KBDocument | null>(null)

  return (
    <div className="space-y-6">
      <UploadDropZone
        onUploadComplete={onRefresh}
        tierLimits={tierLimits}
        showToast={showToast}
      />

      {/* Document list */}
      {loading ? (
        <div className="animate-pulse space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-12 bg-gray-200 dark:bg-gray-800 rounded" />
          ))}
        </div>
      ) : documents.length === 0 ? (
        <div className="text-center py-12 text-gray-400 dark:text-gray-500">
          <DocumentTextIcon className="h-12 w-12 mx-auto mb-3 opacity-50" />
          <p>No documents yet. Upload your first document above.</p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-lg border border-gray-200 dark:border-gray-700">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-800">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Document
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Type
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Chunks
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Size
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
              {documents.map((doc) => {
                const ext = doc.file_type.toLowerCase()
                const typeConfig = FILE_TYPE_CONFIG[ext]
                return (
                  <tr
                    key={doc.id}
                    onClick={() => setSelectedDoc(doc)}
                    className="cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
                  >
                    <td className="px-4 py-3 text-sm text-gray-900 dark:text-gray-100">
                      {doc.title || doc.filename}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`text-sm font-medium uppercase ${typeConfig?.color || 'text-gray-500 dark:text-gray-400'}`}
                      >
                        {typeConfig?.label || ext}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">
                      {doc.chunk_count}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">
                      {formatBytes(doc.file_size_bytes)}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                          doc.status === 'ready'
                            ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                            : doc.status === 'processing'
                              ? 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400'
                              : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
                        }`}
                      >
                        {doc.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation()
                          confirmDelete(doc.id, doc.filename)
                        }}
                        className="text-gray-400 hover:text-red-500 transition-colors"
                        aria-label={`Delete ${doc.filename}`}
                      >
                        <TrashIcon className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      <DocumentDetailModal
        document={selectedDoc}
        isOpen={selectedDoc !== null}
        onClose={() => setSelectedDoc(null)}
        onDelete={(docId, filename) => {
          setSelectedDoc(null)
          confirmDelete(docId, filename)
        }}
      />
    </div>
  )
}
