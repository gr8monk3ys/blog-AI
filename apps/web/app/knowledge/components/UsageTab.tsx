'use client'

import { m } from 'framer-motion'
import type { KBStatsWithLimits } from '../../../types/knowledge'
import { FILE_TYPE_CONFIG, formatBytes } from '../../../types/knowledge'
import { TIER_DISPLAY, type UsageTier } from '../../../types/usage'

interface UsageTabProps {
  stats: KBStatsWithLimits | null
}

function UsageBar({
  current,
  max,
  label,
  formatValue,
}: {
  current: number
  max: number | null
  label: string
  formatValue: (n: number) => string
}) {
  const isUnlimited = max == null
  const percentage = isUnlimited ? 0 : max > 0 ? (current / max) * 100 : 0
  const barColor =
    percentage >= 90 ? 'bg-red-500' : percentage >= 70 ? 'bg-amber-500' : 'bg-green-500'

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-sm">
        <span className="text-gray-600 dark:text-gray-400">{label}</span>
        {isUnlimited ? (
          <span className="font-medium text-gray-900 dark:text-gray-100">
            {formatValue(current)} / Unlimited
          </span>
        ) : (
          <span className="font-medium text-gray-900 dark:text-gray-100">
            {formatValue(current)} / {formatValue(max)}
          </span>
        )}
      </div>
      {!isUnlimited && (
        <div className="w-full bg-gray-200 dark:bg-gray-800 rounded-full h-2">
          <m.div
            initial={{ width: 0 }}
            animate={{ width: `${Math.min(percentage, 100)}%` }}
            className={`h-2 rounded-full ${barColor}`}
          />
        </div>
      )}
    </div>
  )
}

export default function UsageTab({ stats }: UsageTabProps) {
  if (!stats) {
    return (
      <div className="text-center py-12 text-gray-400 dark:text-gray-500">
        <p>Unable to load usage data.</p>
      </div>
    )
  }

  const limits = stats.tier_limits
  const tier = (limits?.tier || 'free') as UsageTier
  const tierDisplay = TIER_DISPLAY[tier] || TIER_DISPLAY.free

  const docPercentage =
    limits?.max_documents != null && limits.max_documents > 0
      ? (limits.current_documents / limits.max_documents) * 100
      : 0
  const storagePercentage =
    limits?.max_storage_bytes != null && limits.max_storage_bytes > 0
      ? (limits.current_storage_bytes / limits.max_storage_bytes) * 100
      : 0

  const showWarning = docPercentage >= 80 || storagePercentage >= 80
  const showCritical = docPercentage >= 100 || storagePercentage >= 100
  const showUpgradeCTA = tier === 'free' || tier === 'starter'

  return (
    <div className="space-y-6">
      {/* Tier badge */}
      <div className="flex items-center gap-3">
        <span
          className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold ${tierDisplay.bgColor} ${tierDisplay.color} dark:bg-opacity-20`}
        >
          {tierDisplay.name} Plan
        </span>
      </div>

      {/* Warning banners */}
      {showCritical && (
        <div className="px-4 py-3 rounded-lg bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800 text-sm text-red-700 dark:text-red-400">
          You&apos;ve reached your plan limits. Upgrade to continue uploading documents.
        </div>
      )}
      {showWarning && !showCritical && (
        <div className="px-4 py-3 rounded-lg bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 text-sm text-amber-700 dark:text-amber-400">
          You&apos;re approaching your plan limits. Consider upgrading for more capacity.
        </div>
      )}

      {/* Usage bars */}
      {limits && (
        <div className="space-y-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          <UsageBar
            current={limits.current_documents}
            max={limits.max_documents}
            label="Documents"
            formatValue={(n) => String(n)}
          />
          <UsageBar
            current={limits.current_storage_bytes}
            max={limits.max_storage_bytes}
            label="Storage"
            formatValue={formatBytes}
          />
        </div>
      )}

      {/* Stats overview */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 text-center">
          <p className="text-2xl font-semibold text-amber-600">{stats.total_documents}</p>
          <p className="text-xs text-gray-500 dark:text-gray-400">Documents</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 text-center">
          <p className="text-2xl font-semibold text-amber-600">{stats.total_chunks}</p>
          <p className="text-xs text-gray-500 dark:text-gray-400">Chunks</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 text-center">
          <p className="text-2xl font-semibold text-amber-600">
            {formatBytes(stats.storage_size_bytes)}
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-400">Storage</p>
        </div>
      </div>

      {/* Type breakdown */}
      {Object.keys(stats.documents_by_type).length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            Documents by Type
          </h3>
          <div className="flex flex-wrap gap-2">
            {Object.entries(stats.documents_by_type).map(([type, count]) => {
              const typeConfig = FILE_TYPE_CONFIG[type]
              return (
                <span
                  key={type}
                  className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-700 ${typeConfig?.color || 'text-gray-600 dark:text-gray-400'}`}
                >
                  {typeConfig?.label || type.toUpperCase()}
                  <span className="text-gray-400 dark:text-gray-500">{count}</span>
                </span>
              )
            })}
          </div>
        </div>
      )}

      {/* Upgrade CTA */}
      {showUpgradeCTA && (
        <div className="bg-gradient-to-r from-amber-50 to-orange-50 dark:from-amber-950/20 dark:to-orange-950/20 rounded-lg border border-amber-200 dark:border-amber-800 p-4">
          <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-1">
            Need more capacity?
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
            {tier === 'free'
              ? 'Upgrade to Starter for 20 documents and 50MB storage, or Pro for unlimited.'
              : 'Upgrade to Pro for unlimited documents and storage.'}
          </p>
          <a
            href="/pricing"
            className="inline-flex px-4 py-2 text-sm font-medium text-white bg-amber-600 rounded-lg hover:bg-amber-700 transition-colors"
          >
            View Plans
          </a>
        </div>
      )}
    </div>
  )
}
