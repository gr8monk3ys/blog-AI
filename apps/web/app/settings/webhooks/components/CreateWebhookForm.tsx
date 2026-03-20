'use client'

import { useState } from 'react'
import { XMarkIcon, EyeIcon, EyeSlashIcon } from '@heroicons/react/24/outline'
import { API_ENDPOINTS, getDefaultHeaders } from '../../../../lib/api'
import type { ToastOptions } from '../../../../hooks/useToast'
import type { WebhookSubscription, WebhookEventType } from '../../../../types/webhooks'
import EventTypeSelector from './EventTypeSelector'

interface CreateWebhookFormProps {
  editingSubscription: WebhookSubscription | null
  onClose: () => void
  onSuccess: () => void
  showToast: (opts: ToastOptions) => void
}

export default function CreateWebhookForm({ editingSubscription, onClose, onSuccess, showToast }: CreateWebhookFormProps) {
  const isEditing = !!editingSubscription
  const [targetUrl, setTargetUrl] = useState(editingSubscription?.target_url || '')
  const [eventTypes, setEventTypes] = useState<WebhookEventType[]>(editingSubscription?.event_types || [])
  const [secret, setSecret] = useState('')
  const [showSecret, setShowSecret] = useState(false)
  const [description, setDescription] = useState(editingSubscription?.description || '')
  const [saving, setSaving] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()

    if (eventTypes.length === 0) {
      showToast({ message: 'Select at least one event type.', variant: 'warning' })
      return
    }

    setSaving(true)

    try {
      const headers = await getDefaultHeaders()
      const body: Record<string, unknown> = {
        target_url: targetUrl,
        event_types: eventTypes,
      }
      if (secret) body.secret = secret
      if (description) body.description = description

      let res: Response
      if (isEditing) {
        res = await fetch(API_ENDPOINTS.webhooks.update(editingSubscription.id), {
          method: 'PATCH',
          headers,
          body: JSON.stringify(body),
        })
      } else {
        res = await fetch(API_ENDPOINTS.webhooks.subscribe, {
          method: 'POST',
          headers,
          body: JSON.stringify(body),
        })
      }

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}))
        throw new Error(errData?.detail || errData?.error || `HTTP ${res.status}`)
      }

      showToast({ message: isEditing ? 'Webhook updated.' : 'Webhook created.', variant: 'success' })
      onSuccess()
    } catch (err) {
      showToast({ message: err instanceof Error ? err.message : 'Failed to save webhook.', variant: 'error' })
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          {isEditing ? 'Edit Webhook' : 'New Webhook'}
        </h2>
        <button
          type="button"
          onClick={onClose}
          className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
        >
          <XMarkIcon className="w-5 h-5" />
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        {/* URL */}
        <div>
          <label htmlFor="wh-url" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
            Endpoint URL <span className="text-red-500">*</span>
          </label>
          <input
            id="wh-url"
            type="url"
            value={targetUrl}
            onChange={(e) => setTargetUrl(e.target.value)}
            placeholder="https://your-app.com/webhooks/blog-ai"
            className="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-4 py-2.5 text-sm text-gray-900 dark:text-gray-100 placeholder-gray-400 focus:border-amber-500 focus:ring-1 focus:ring-amber-500 font-mono"
            required
          />
        </div>

        {/* Event types */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Event types <span className="text-red-500">*</span>
          </label>
          <EventTypeSelector selected={eventTypes} onChange={setEventTypes} />
        </div>

        {/* Secret */}
        <div>
          <label htmlFor="wh-secret" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
            Signing secret (optional)
          </label>
          <div className="relative">
            <input
              id="wh-secret"
              type={showSecret ? 'text' : 'password'}
              value={secret}
              onChange={(e) => setSecret(e.target.value)}
              placeholder={isEditing ? 'Leave empty to keep current' : 'Used for HMAC-SHA256 signature verification'}
              className="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-4 py-2.5 pr-10 text-sm text-gray-900 dark:text-gray-100 placeholder-gray-400 focus:border-amber-500 focus:ring-1 focus:ring-amber-500 font-mono"
              maxLength={256}
            />
            <button
              type="button"
              onClick={() => setShowSecret(!showSecret)}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              {showSecret ? <EyeSlashIcon className="w-4 h-4" /> : <EyeIcon className="w-4 h-4" />}
            </button>
          </div>
        </div>

        {/* Description */}
        <div>
          <label htmlFor="wh-desc" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
            Description (optional)
          </label>
          <input
            id="wh-desc"
            type="text"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="What is this webhook for?"
            className="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-4 py-2.5 text-sm text-gray-900 dark:text-gray-100 placeholder-gray-400 focus:border-amber-500 focus:ring-1 focus:ring-amber-500"
            maxLength={500}
          />
        </div>

        {/* Actions */}
        <div className="flex items-center gap-3 pt-2">
          <button
            type="submit"
            disabled={saving}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-medium bg-amber-600 text-white hover:bg-amber-700 disabled:bg-gray-300 dark:disabled:bg-gray-700 disabled:cursor-not-allowed transition-colors"
          >
            {saving ? 'Saving...' : isEditing ? 'Update Webhook' : 'Create Webhook'}
          </button>
          <button
            type="button"
            onClick={onClose}
            className="px-5 py-2.5 rounded-lg text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 transition-colors"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  )
}
