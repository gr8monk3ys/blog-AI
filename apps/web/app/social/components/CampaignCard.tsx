'use client'

import { PauseIcon, PlayIcon, XMarkIcon } from '@heroicons/react/24/outline'
import type { Campaign } from '../../../types/social'
import PlatformIcon from './PlatformIcon'

interface CampaignCardProps {
  campaign: Campaign
  onPause: (id: string) => void
  onResume: (id: string) => void
  onCancel: (id: string) => void
}

const STATUS_STYLES: Record<string, string> = {
  draft: 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400',
  active: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300',
  paused: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300',
  completed: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300',
  cancelled: 'bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400',
}

export default function CampaignCard({ campaign, onPause, onResume, onCancel }: CampaignCardProps) {
  const canPause = campaign.status === 'active'
  const canResume = campaign.status === 'paused'
  const canCancel = campaign.status === 'active' || campaign.status === 'paused' || campaign.status === 'draft'

  return (
    <div className="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 mb-1">
            <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100 truncate">{campaign.name}</h4>
            <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_STYLES[campaign.status] || STATUS_STYLES.draft}`}>
              {campaign.status}
            </span>
          </div>
          {campaign.description && (
            <p className="text-xs text-gray-500 dark:text-gray-400 mb-2 line-clamp-1">{campaign.description}</p>
          )}

          {/* Platforms */}
          <div className="flex items-center gap-2 mb-2">
            {campaign.platforms.map((pc) => (
              <PlatformIcon key={pc.platform} platform={pc.platform} size="sm" />
            ))}
          </div>

          {/* Stats row */}
          <div className="flex flex-wrap gap-3 text-xs text-gray-500 dark:text-gray-400">
            <span>{campaign.post_count} post{campaign.post_count !== 1 ? 's' : ''}</span>
            {campaign.scheduled_at && (
              <span>Scheduled: {new Date(campaign.scheduled_at).toLocaleDateString()}</span>
            )}
            {campaign.tags && campaign.tags.length > 0 && (
              <span className="flex gap-1">
                {campaign.tags.map((tag) => (
                  <span key={tag} className="px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300">
                    {tag}
                  </span>
                ))}
              </span>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-1.5 shrink-0">
          {canPause && (
            <button
              type="button"
              onClick={() => onPause(campaign.id)}
              className="p-1.5 rounded-lg text-gray-400 hover:text-amber-600 dark:hover:text-amber-400 hover:bg-amber-50 dark:hover:bg-amber-900/20 transition-colors"
              title="Pause campaign"
            >
              <PauseIcon className="w-4 h-4" />
            </button>
          )}
          {canResume && (
            <button
              type="button"
              onClick={() => onResume(campaign.id)}
              className="p-1.5 rounded-lg text-gray-400 hover:text-emerald-600 dark:hover:text-emerald-400 hover:bg-emerald-50 dark:hover:bg-emerald-900/20 transition-colors"
              title="Resume campaign"
            >
              <PlayIcon className="w-4 h-4" />
            </button>
          )}
          {canCancel && (
            <button
              type="button"
              onClick={() => onCancel(campaign.id)}
              className="p-1.5 rounded-lg text-gray-400 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
              title="Cancel campaign"
            >
              <XMarkIcon className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
