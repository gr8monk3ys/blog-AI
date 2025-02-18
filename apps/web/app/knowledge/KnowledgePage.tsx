'use client'

import { useCallback, useEffect, useState } from 'react'
import { Tab } from '@headlessui/react'
import { DocumentTextIcon } from '@heroicons/react/24/outline'
import { API_ENDPOINTS, apiFetch } from '../../lib/api'
import { useToast } from '../../hooks/useToast'
import { useConfirmModal } from '../../hooks/useConfirmModal'
import type { KBDocument, KBStatsWithLimits } from '../../types/knowledge'
import DocumentsTab from './components/DocumentsTab'
import SearchTab from './components/SearchTab'
import UsageTab from './components/UsageTab'

function classNames(...classes: string[]) {
  return classes.filter(Boolean).join(' ')
}

export default function KnowledgePage() {
  const [documents, setDocuments] = useState<KBDocument[]>([])
  const [stats, setStats] = useState<KBStatsWithLimits | null>(null)
  const [loading, setLoading] = useState(true)
  const [backendError, setBackendError] = useState<string | null>(null)

  const { showToast, ToastComponent } = useToast()
  const { confirm, ConfirmModalComponent } = useConfirmModal()

  const fetchDocuments = useCallback(async () => {
    try {
      const data = await apiFetch<{ documents: KBDocument[] }>(
        API_ENDPOINTS.knowledge.documents
      )
      setDocuments(data.documents || [])
    } catch {
      setDocuments([])
      setBackendError('Knowledge Base requires database setup. Please ensure migrations have been applied.')
    }
  }, [])

  const fetchStats = useCallback(async () => {
    try {
      const data = await apiFetch<KBStatsWithLimits>(API_ENDPOINTS.knowledge.stats)
      setStats(data)
    } catch {
      setStats(null)
      setBackendError('Knowledge Base requires database setup. Please ensure migrations have been applied.')
    }
  }, [])

  const refresh = useCallback(async () => {
    await Promise.all([fetchDocuments(), fetchStats()])
  }, [fetchDocuments, fetchStats])

  useEffect(() => {
    refresh().finally(() => setLoading(false))
  }, [refresh])

  const handleDelete = useCallback(
    async (docId: string, filename: string) => {
      const confirmed = await confirm({
        title: `Delete "${filename}"?`,
        message: 'This will permanently remove the document and all its chunks. This action cannot be undone.',
        variant: 'danger',
        confirmLabel: 'Delete',
      })
      if (!confirmed) return

      try {
        await apiFetch(API_ENDPOINTS.knowledge.document(docId), {
          method: 'DELETE',
        })
        showToast({ message: `Deleted "${filename}"`, variant: 'success' })
        await refresh()
      } catch (err) {
        showToast({
          message: err instanceof Error ? err.message : 'Delete failed',
          variant: 'error',
        })
      }
    },
    [confirm, showToast, refresh]
  )

  const tabNames = ['Documents', 'Search', 'Usage']

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="flex items-center mb-2">
        <DocumentTextIcon className="h-6 w-6 text-amber-600 mr-2" />
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
          Knowledge Base
        </h1>
      </div>

      <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
        Upload company documents (style guides, product specs, research) so the
        AI can reference them during blog generation.
      </p>

      {backendError && (
        <div className="glass-card rounded-2xl p-8 text-center mb-6">
          <p className="text-sm font-medium text-gray-700 dark:text-gray-300">Knowledge Base Unavailable</p>
          <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">{backendError}</p>
        </div>
      )}

      <Tab.Group>
        <Tab.List className="flex space-x-1 rounded-lg bg-gray-100 dark:bg-gray-800 p-1 mb-6">
          {tabNames.map((tab) => (
            <Tab
              key={tab}
              className={({ selected }) =>
                classNames(
                  'w-full rounded-md py-2 text-sm font-medium leading-5 transition-colors',
                  selected
                    ? 'bg-white dark:bg-gray-900 text-amber-700 dark:text-amber-400 shadow'
                    : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
                )
              }
            >
              {tab}
            </Tab>
          ))}
        </Tab.List>
        <Tab.Panels>
          <Tab.Panel>
            <DocumentsTab
              documents={documents}
              loading={loading}
              tierLimits={stats?.tier_limits}
              onRefresh={refresh}
              showToast={showToast}
              confirmDelete={handleDelete}
            />
          </Tab.Panel>
          <Tab.Panel>
            <SearchTab documents={documents} />
          </Tab.Panel>
          <Tab.Panel>
            <UsageTab stats={stats} />
          </Tab.Panel>
        </Tab.Panels>
      </Tab.Group>

      <ToastComponent />
      <ConfirmModalComponent />
    </div>
  )
}
