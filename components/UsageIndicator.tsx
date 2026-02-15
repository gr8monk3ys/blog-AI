'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'
import {
  ChartBarIcon,
  ArrowUpCircleIcon,
  ExclamationTriangleIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline'
import { UsageStats, TIER_DISPLAY } from '../types/usage'
import { API_ENDPOINTS, getDefaultHeaders } from '../lib/api'

interface UsageIndicatorProps {
  compact?: boolean
  showUpgradePrompt?: boolean
  onLimitReached?: () => void
}

export default function UsageIndicator({
  compact = false,
  showUpgradePrompt = true,
  onLimitReached,
}: UsageIndicatorProps) {
  const [usage, setUsage] = useState<UsageStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showDetails, setShowDetails] = useState(false)

  useEffect(() => {
    fetchUsageStats()
    // Refresh usage stats every 30 seconds
    const interval = setInterval(fetchUsageStats, 30000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    if (!usage || !onLimitReached) return
    const atLimit =
      usage.is_quota_exceeded ||
      (usage.daily_limit !== -1 && usage.daily_remaining <= 0) ||
      (usage.quota_limit !== -1 && usage.remaining <= 0)
    if (atLimit) onLimitReached()
  }, [usage, onLimitReached])

  const fetchUsageStats = async () => {
    try {
      const response = await fetch(API_ENDPOINTS.usage.stats, {
        headers: await getDefaultHeaders(),
      })

      if (!response.ok) {
        throw new Error('Failed to fetch usage stats')
      }

      const data = await response.json()
      setUsage(data)
      setError(null)
    } catch (err) {
      console.error('Error fetching usage stats:', err)
      setError('Unable to load usage')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="animate-pulse flex items-center gap-2">
        <div className="h-4 w-4 bg-gray-200 rounded" />
        <div className="h-4 w-16 bg-gray-200 rounded" />
      </div>
    )
  }

  if (error || !usage) {
    return null // Silently hide if there's an error
  }

  const isDailyUnlimited = usage.daily_limit === -1
  const isMonthlyUnlimited = usage.quota_limit === -1
  const dailyPercentUsed = isDailyUnlimited || usage.daily_limit <= 0
    ? 0
    : (usage.daily_usage / usage.daily_limit) * 100
  const monthlyPercentUsed = typeof usage.percentage_used === 'number'
    ? usage.percentage_used
    : (!isMonthlyUnlimited && usage.quota_limit > 0 ? (usage.current_usage / usage.quota_limit) * 100 : 0)

  const isNearLimit = (!isDailyUnlimited && dailyPercentUsed >= 80) || (!isMonthlyUnlimited && monthlyPercentUsed >= 80)
  const isAtLimit =
    usage.is_quota_exceeded ||
    (!isDailyUnlimited && usage.daily_remaining <= 0) ||
    (!isMonthlyUnlimited && usage.remaining <= 0)

  // Compact version for header
  if (compact) {
    const compactLabel = (() => {
      if (isDailyUnlimited && isMonthlyUnlimited) return 'Unlimited'
      if (!isDailyUnlimited) return `${usage.daily_remaining}/${usage.daily_limit}`
      // Daily unlimited, show monthly remaining.
      return isMonthlyUnlimited ? 'Unlimited' : `${usage.remaining}/${usage.quota_limit}`
    })()

    return (
      <div className="relative">
        <button
          onClick={() => setShowDetails(!showDetails)}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg transition-colors ${
            isAtLimit
              ? 'bg-red-100 text-red-700 hover:bg-red-200'
              : isNearLimit
              ? 'bg-amber-100 text-amber-700 hover:bg-amber-200'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          <ChartBarIcon className="h-4 w-4" />
          <span className="text-sm font-medium">{compactLabel}</span>
        </button>

        <AnimatePresence>
          {showDetails && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="absolute right-0 mt-2 w-72 bg-white rounded-xl shadow-lg border border-gray-200 p-4 z-50"
            >
              <UsageDetails usage={usage} showUpgradePrompt={showUpgradePrompt} />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    )
  }

  // Full version
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4">
      <UsageDetails usage={usage} showUpgradePrompt={showUpgradePrompt} />
    </div>
  )
}

interface UsageDetailsProps {
  usage: UsageStats
  showUpgradePrompt: boolean
}

function UsageDetails({ usage, showUpgradePrompt }: UsageDetailsProps) {
  const tierDisplay = TIER_DISPLAY[usage.tier]
  const isDailyUnlimited = usage.daily_limit === -1
  const isMonthlyUnlimited = usage.quota_limit === -1
  const dailyPercentUsed = isDailyUnlimited || usage.daily_limit <= 0
    ? 0
    : (usage.daily_usage / usage.daily_limit) * 100
  const monthlyPercentUsed = typeof usage.percentage_used === 'number'
    ? usage.percentage_used
    : (!isMonthlyUnlimited && usage.quota_limit > 0 ? (usage.current_usage / usage.quota_limit) * 100 : 0)

  const isNearLimit = (!isDailyUnlimited && dailyPercentUsed >= 80) || (!isMonthlyUnlimited && monthlyPercentUsed >= 80)
  const isAtLimit =
    usage.is_quota_exceeded ||
    (!isDailyUnlimited && usage.daily_remaining <= 0) ||
    (!isMonthlyUnlimited && usage.remaining <= 0)

  return (
    <div className="space-y-4">
      {/* Header with tier badge */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <SparklesIcon className={`h-5 w-5 ${tierDisplay.color}`} />
          <span className="font-semibold text-gray-900">Usage</span>
        </div>
        <span
          className={`px-2 py-0.5 rounded-full text-xs font-medium ${tierDisplay.bgColor} ${tierDisplay.color}`}
        >
          {tierDisplay.name}
        </span>
      </div>

      {/* Daily usage */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">Today</span>
          {isDailyUnlimited ? (
            <span className="font-medium text-gray-900">Unlimited</span>
          ) : (
            <span className="font-medium text-gray-900">
              {usage.daily_usage} / {usage.daily_limit}
            </span>
          )}
        </div>
        {!isDailyUnlimited && (
          <div className="w-full bg-gray-200 rounded-full h-2">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${Math.min(dailyPercentUsed, 100)}%` }}
              className={`h-2 rounded-full ${
                isAtLimit
                  ? 'bg-red-500'
                  : isNearLimit
                  ? 'bg-amber-500'
                  : 'bg-amber-500'
              }`}
            />
          </div>
        )}
      </div>

      {/* Monthly usage */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">This period</span>
          {isMonthlyUnlimited ? (
            <span className="font-medium text-gray-900">Unlimited</span>
          ) : (
            <span className="font-medium text-gray-900">
              {usage.current_usage} / {usage.quota_limit}
            </span>
          )}
        </div>
        {!isMonthlyUnlimited && (
          <div className="w-full bg-gray-200 rounded-full h-2">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${Math.min(monthlyPercentUsed, 100)}%` }}
              className={`h-2 rounded-full ${
                monthlyPercentUsed >= 100
                  ? 'bg-red-500'
                  : monthlyPercentUsed >= 80
                  ? 'bg-amber-500'
                  : 'bg-amber-500'
              }`}
            />
          </div>
        )}
      </div>

      {/* Warning message */}
      {isAtLimit && (
        <div className="flex items-start gap-2 p-3 bg-red-50 rounded-lg border border-red-200">
          <ExclamationTriangleIcon className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
          <div className="text-sm">
            <p className="font-medium text-red-800">Limit reached</p>
            <p className="text-red-600">
              Upgrade to continue generating content
            </p>
          </div>
        </div>
      )}

      {isNearLimit && !isAtLimit && (
        <div className="flex items-start gap-2 p-3 bg-amber-50 rounded-lg border border-amber-200">
          <ExclamationTriangleIcon className="h-5 w-5 text-amber-500 flex-shrink-0 mt-0.5" />
          <div className="text-sm">
            <p className="font-medium text-amber-800">Running low</p>
            <p className="text-amber-600">
              {!isDailyUnlimited
                ? `${usage.daily_remaining} generations remaining today`
                : !isMonthlyUnlimited
                ? `${usage.remaining} generations remaining this period`
                : 'Unlimited usage'}
            </p>
          </div>
        </div>
      )}

      {/* Upgrade prompt */}
      {showUpgradePrompt && usage.tier !== 'pro' && usage.tier !== 'business' && (
        <Link
          href="/pricing"
          className="flex items-center justify-center gap-2 w-full py-2 px-4 bg-gradient-to-r from-amber-600 to-amber-700 hover:from-amber-700 hover:to-amber-800 text-white text-sm font-medium rounded-lg transition-all"
        >
          <ArrowUpCircleIcon className="h-4 w-4" />
          {usage.tier === 'free' ? 'Upgrade to Starter' : 'Upgrade to Pro'}
        </Link>
      )}

      {/* Reset time */}
      <p className="text-xs text-gray-500 text-center">
        Resets daily at midnight UTC
      </p>
    </div>
  )
}

// Export a hook for checking usage before generation
export function useUsageCheck() {
  const [canGenerate, setCanGenerate] = useState(true)
  const [remaining, setRemaining] = useState<number | null>(null)
  const [loading, setLoading] = useState(false)

  const checkUsage = async (): Promise<boolean> => {
    setLoading(true)
    try {
      const response = await fetch(API_ENDPOINTS.usage.check, {
        headers: await getDefaultHeaders(),
      })

      if (response.status === 429) {
        setCanGenerate(false)
        setRemaining(0)
        return false
      }

      if (!response.ok) {
        // Allow generation if we can't check (fail open for dev mode)
        return true
      }

      const data = await response.json()
      setCanGenerate(!!data.has_quota)
      // Prefer daily remaining if present; fallback to period remaining.
      const rem =
        typeof data.daily_remaining === 'number'
          ? data.daily_remaining
          : typeof data.remaining === 'number'
          ? data.remaining
          : null
      setRemaining(rem)
      return !!data.has_quota
    } catch (err) {
      console.error('Error checking usage:', err)
      // Fail open for development
      return true
    } finally {
      setLoading(false)
    }
  }

  return { canGenerate, remaining, loading, checkUsage }
}
