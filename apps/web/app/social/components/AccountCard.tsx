'use client'

import { TrashIcon } from '@heroicons/react/24/outline'
import type { SocialAccount } from '../../../types/social'
import { PLATFORM_CONFIG } from '../../../types/social'
import PlatformIcon from './PlatformIcon'

interface AccountCardProps {
  account: SocialAccount
  onDisconnect: (id: string) => void
}

export default function AccountCard({ account, onDisconnect }: AccountCardProps) {
  const config = PLATFORM_CONFIG[account.platform]

  return (
    <div className={`rounded-xl border p-5 transition-colors ${
      account.is_active
        ? 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800'
        : 'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 opacity-70'
    }`}>
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <PlatformIcon platform={account.platform} />
          <div>
            <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
              {account.display_name || account.username}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              @{account.username} &middot; {config.name}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
            account.is_active
              ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300'
              : 'bg-gray-100 text-gray-500 dark:bg-gray-800 dark:text-gray-400'
          }`}>
            {account.is_active ? 'Connected' : 'Inactive'}
          </span>
          <button
            type="button"
            onClick={() => onDisconnect(account.id)}
            className="p-1.5 rounded-lg text-gray-400 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
            title="Disconnect"
          >
            <TrashIcon className="w-4 h-4" />
          </button>
        </div>
      </div>
      <div className="mt-3 text-xs text-gray-400 dark:text-gray-500">
        Connected {new Date(account.connected_at).toLocaleDateString()}
        {account.last_used_at && (
          <> &middot; Last used {new Date(account.last_used_at).toLocaleDateString()}</>
        )}
      </div>
    </div>
  )
}
