'use client'

import { PencilSquareIcon, TrashIcon } from '@heroicons/react/24/outline'
import type { WebhookSubscription } from '../../../../types/webhooks'
import type { ToastOptions } from '../../../../hooks/useToast'
import TestWebhookButton from './TestWebhookButton'

interface SubscriptionCardProps {
  subscription: WebhookSubscription
  onEdit: (sub: WebhookSubscription) => void
  onDelete: (id: string) => void
  onToggleActive: (sub: WebhookSubscription) => void
  showToast: (opts: ToastOptions) => void
}

export default function SubscriptionCard({ subscription: sub, onEdit, onDelete, onToggleActive, showToast }: SubscriptionCardProps) {
  const successRate = sub.total_deliveries > 0
    ? Math.round((sub.successful_deliveries / sub.total_deliveries) * 100)
    : null

  return (
    <div className={`rounded-xl border p-5 transition-colors ${
      sub.is_active
        ? 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800'
        : 'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 opacity-70'
    }`}>
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          {/* URL */}
          <div className="flex items-center gap-2 mb-2">
            <code className="text-sm font-mono text-gray-900 dark:text-gray-100 truncate block">
              {sub.target_url}
            </code>
            <span className={`shrink-0 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
              sub.is_active
                ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300'
                : 'bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400'
            }`}>
              {sub.is_active ? 'Active' : 'Inactive'}
            </span>
          </div>

          {/* Description */}
          {sub.description && (
            <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">{sub.description}</p>
          )}

          {/* Event type badges */}
          <div className="flex flex-wrap gap-1.5 mb-3">
            {sub.event_types.map((type) => (
              <span
                key={type}
                className="px-2 py-0.5 rounded text-xs font-mono bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300"
              >
                {type}
              </span>
            ))}
          </div>

          {/* Delivery stats */}
          <div className="flex flex-wrap gap-4 text-xs text-gray-500 dark:text-gray-400">
            <span>Total: {sub.total_deliveries}</span>
            <span className="text-emerald-600 dark:text-emerald-400">Success: {sub.successful_deliveries}</span>
            <span className="text-red-600 dark:text-red-400">Failed: {sub.failed_deliveries}</span>
            {successRate !== null && (
              <span>{successRate}% success rate</span>
            )}
            {sub.last_delivery_at && (
              <span>Last: {new Date(sub.last_delivery_at).toLocaleDateString()}</span>
            )}
          </div>

          {/* Last error */}
          {sub.last_error && (
            <p className="mt-2 text-xs text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 rounded px-2 py-1 border border-red-200 dark:border-red-800">
              Last error: {sub.last_error}
            </p>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2 shrink-0">
          <TestWebhookButton subscriptionId={sub.id} showToast={showToast} />
          <button
            type="button"
            onClick={() => onToggleActive(sub)}
            className="px-3 py-1.5 rounded-lg text-xs font-medium border border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          >
            {sub.is_active ? 'Deactivate' : 'Activate'}
          </button>
          <button
            type="button"
            onClick={() => onEdit(sub)}
            className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            title="Edit"
          >
            <PencilSquareIcon className="w-4 h-4" />
          </button>
          <button
            type="button"
            onClick={() => onDelete(sub.id)}
            className="p-1.5 rounded-lg text-gray-400 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
            title="Delete"
          >
            <TrashIcon className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  )
}
