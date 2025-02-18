'use client'

import { useState, useEffect, useCallback } from 'react'
import { BoltIcon, PlusIcon } from '@heroicons/react/24/outline'
import { AnimatePresence, motion } from 'framer-motion'
import { API_ENDPOINTS, getDefaultHeaders } from '../../../lib/api'
import { useToast } from '../../../hooks/useToast'
import { useConfirmModal } from '../../../hooks/useConfirmModal'
import type { WebhookSubscription } from '../../../types/webhooks'
import SubscriptionCard from './components/SubscriptionCard'
import CreateWebhookForm from './components/CreateWebhookForm'
import EventTypeReference from './components/EventTypeReference'

export default function WebhooksPageClient() {
  const [subscriptions, setSubscriptions] = useState<WebhookSubscription[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [editingSubscription, setEditingSubscription] = useState<WebhookSubscription | null>(null)
  const { showToast, ToastComponent } = useToast()
  const { confirm, ConfirmModalComponent } = useConfirmModal()

  const fetchSubscriptions = useCallback(async () => {
    try {
      const headers = await getDefaultHeaders()
      const res = await fetch(API_ENDPOINTS.webhooks.list, { headers })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setSubscriptions(Array.isArray(data) ? data : data.subscriptions || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load webhooks.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchSubscriptions()
  }, [fetchSubscriptions])

  async function handleDelete(id: string) {
    const confirmed = await confirm({
      title: 'Delete webhook?',
      message: 'This will permanently remove the subscription and stop all deliveries.',
      variant: 'danger',
      confirmLabel: 'Delete',
    })
    if (!confirmed) return

    try {
      const headers = await getDefaultHeaders()
      const res = await fetch(API_ENDPOINTS.webhooks.delete(id), { method: 'DELETE', headers })
      if (!res.ok && res.status !== 204) throw new Error(`HTTP ${res.status}`)
      setSubscriptions((prev) => prev.filter((s) => s.id !== id))
      showToast({ message: 'Webhook deleted.', variant: 'success' })
    } catch {
      showToast({ message: 'Failed to delete webhook.', variant: 'error' })
    }
  }

  async function handleToggleActive(sub: WebhookSubscription) {
    try {
      const headers = await getDefaultHeaders()
      const endpoint = sub.is_active
        ? API_ENDPOINTS.webhooks.deactivate(sub.id)
        : API_ENDPOINTS.webhooks.activate(sub.id)
      const res = await fetch(endpoint, { method: 'POST', headers })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      setSubscriptions((prev) =>
        prev.map((s) => (s.id === sub.id ? { ...s, is_active: !s.is_active } : s))
      )
      showToast({ message: sub.is_active ? 'Webhook deactivated.' : 'Webhook activated.', variant: 'success' })
    } catch {
      showToast({ message: 'Failed to update webhook.', variant: 'error' })
    }
  }

  function handleEdit(sub: WebhookSubscription) {
    setEditingSubscription(sub)
    setShowForm(true)
  }

  function handleFormClose() {
    setShowForm(false)
    setEditingSubscription(null)
  }

  function handleFormSuccess() {
    handleFormClose()
    fetchSubscriptions()
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-3">
          <div className="inline-flex items-center justify-center w-11 h-11 rounded-xl bg-amber-100/80 dark:bg-amber-900/40 text-amber-700">
            <BoltIcon className="w-5 h-5" aria-hidden="true" />
          </div>
          <div>
            <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">Webhooks</h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">Manage event subscriptions for your content pipeline</p>
          </div>
        </div>
        {!showForm && (
          <button
            type="button"
            onClick={() => { setEditingSubscription(null); setShowForm(true) }}
            className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-lg text-sm font-medium bg-amber-600 text-white hover:bg-amber-700 transition-colors"
          >
            <PlusIcon className="w-4 h-4" />
            Add Webhook
          </button>
        )}
      </div>

      {error && (
        <div className="mb-6 rounded-lg border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20 px-4 py-3 text-sm text-red-700 dark:text-red-300">
          {error}
        </div>
      )}

      {/* Create/Edit form */}
      <AnimatePresence mode="wait">
        {showForm && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
            className="mb-8 overflow-hidden"
          >
            <CreateWebhookForm
              editingSubscription={editingSubscription}
              onClose={handleFormClose}
              onSuccess={handleFormSuccess}
              showToast={showToast}
            />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Subscription list */}
      {loading ? (
        <div className="space-y-4">
          {[1, 2].map((n) => (
            <div key={n} className="rounded-xl border border-gray-200 dark:border-gray-700 p-6 animate-pulse">
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/3 mb-3" />
              <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-2/3" />
            </div>
          ))}
        </div>
      ) : subscriptions.length === 0 ? (
        <div className="text-center py-16">
          <BoltIcon className="w-12 h-12 mx-auto text-gray-300 dark:text-gray-600 mb-4" />
          <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-1">No webhooks configured</h3>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Add a webhook to receive real-time notifications when events occur.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {subscriptions.map((sub) => (
            <SubscriptionCard
              key={sub.id}
              subscription={sub}
              onEdit={handleEdit}
              onDelete={handleDelete}
              onToggleActive={handleToggleActive}
              showToast={showToast}
            />
          ))}
        </div>
      )}

      {/* Event type reference */}
      <EventTypeReference />

      <ToastComponent />
      <ConfirmModalComponent />
    </div>
  )
}
