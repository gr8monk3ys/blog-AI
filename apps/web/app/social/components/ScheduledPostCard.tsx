'use client'

import { XMarkIcon } from '@heroicons/react/24/outline'
import type { ScheduledPost } from '../../../types/social'
import PlatformIcon from './PlatformIcon'

interface ScheduledPostCardProps {
  post: ScheduledPost
  onCancel: (id: string) => void
}

const STATUS_STYLES: Record<string, string> = {
  draft: 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400',
  scheduled: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300',
  publishing: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300',
  published: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300',
  failed: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300',
  cancelled: 'bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400',
}

export default function ScheduledPostCard({ post, onCancel }: ScheduledPostCardProps) {
  const canCancel = post.status === 'scheduled' || post.status === 'draft'

  return (
    <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3 min-w-0 flex-1">
          <PlatformIcon platform={post.platform} size="sm" />
          <div className="min-w-0 flex-1">
            <p className="text-sm text-gray-900 dark:text-gray-100 line-clamp-2">{post.content.text}</p>
            <div className="flex flex-wrap items-center gap-2 mt-2 text-xs text-gray-500 dark:text-gray-400">
              <span className={`px-2 py-0.5 rounded-full font-medium ${STATUS_STYLES[post.status] || STATUS_STYLES.draft}`}>
                {post.status}
              </span>
              <span>{new Date(post.scheduled_at).toLocaleString()}</span>
              {post.recurrence !== 'none' && (
                <span className="capitalize">{post.recurrence}</span>
              )}
            </div>
            {post.error_message && (
              <p className="mt-1 text-xs text-red-600 dark:text-red-400">{post.error_message}</p>
            )}
          </div>
        </div>
        {canCancel && (
          <button
            type="button"
            onClick={() => onCancel(post.id)}
            className="p-1.5 rounded-lg text-gray-400 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors shrink-0"
            title="Cancel post"
          >
            <XMarkIcon className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  )
}
