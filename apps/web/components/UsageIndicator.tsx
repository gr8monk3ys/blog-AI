'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import Link from 'next/link'
import { ChartBarIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline'
import { UsageStats, TIER_DISPLAY } from '../types/usage'
import { API_ENDPOINTS, getDefaultHeaders } from '../lib/api'
import { Badge } from './ui/Badge'
import { buttonVariants } from './ui/Button'
import { cn } from '../lib/cn'

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

  const consecutiveErrors = useRef(0)

  const fetchUsageStats = useCallback(async (signal?: AbortSignal) => {
    try {
      const response = await fetch(API_ENDPOINTS.usage.stats, {
        headers: await getDefaultHeaders(),
        signal,
      })

      if (!response.ok) {
        throw new Error('Failed to fetch usage stats')
      }

      const data = await response.json()
      setUsage(data)
      setError(null)
      consecutiveErrors.current = 0
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') return
      console.error('Error fetching usage stats:', err)
      setError('Unable to load usage')
      consecutiveErrors.current += 1
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    const controller = new AbortController()
    fetchUsageStats(controller.signal)
    const interval = setInterval(() => {
      if (consecutiveErrors.current >= 3) return
      fetchUsageStats(controller.signal)
    }, 30000)
    return () => {
      controller.abort()
      clearInterval(interval)
    }
  }, [fetchUsageStats])

  useEffect(() => {
    if (!usage || !onLimitReached) return
    const atLimit =
      usage.is_quota_exceeded ||
      (usage.daily_limit !== -1 && usage.daily_remaining <= 0) ||
      (usage.quota_limit !== -1 && usage.remaining <= 0)
    if (atLimit) onLimitReached()
  }, [usage, onLimitReached])

  if (loading) {
    return (
      <div className="flex animate-pulse items-center gap-2">
        <div className="h-4 w-4 rounded-sm bg-muted" />
        <div className="h-4 w-16 rounded-sm bg-muted" />
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
          type="button"
          onClick={() => setShowDetails(!showDetails)}
          aria-expanded={showDetails}
          className={cn(
            'cta-secondary rounded-lg px-3 py-1.5 gap-2 font-mono text-sm tabular-nums',
            isAtLimit ? 'text-destructive hover:text-destructive' : isNearLimit ? 'text-warning hover:text-warning' : ''
          )}
        >
          <ChartBarIcon aria-hidden="true" className="h-4 w-4" />
          <span>{compactLabel}</span>
        </button>

        {showDetails && (
          <div className="absolute right-0 z-50 mt-2 w-72 rounded-xl border border-border bg-popover p-4 text-popover-foreground">
            <UsageDetails usage={usage} showUpgradePrompt={showUpgradePrompt} />
          </div>
        )}
      </div>
    )
  }

  // Full version
  return (
    <div className="rounded-xl border border-border bg-card p-4 text-card-foreground">
      <UsageDetails usage={usage} showUpgradePrompt={showUpgradePrompt} />
    </div>
  )
}

interface UsageDetailsProps {
  usage: UsageStats
  showUpgradePrompt: boolean
}

/**
 * A quota bar: tinted paper with the used share in the ink, Warning from 80%
 * and Error at the limit. Width is set inline so there is no mount animation
 * (DESIGN.md → Motion).
 */
function QuotaBar({ percent, label }: { percent: number; label: string }) {
  const clamped = Math.min(Math.max(percent, 0), 100)
  return (
    <div
      className="h-1.5 w-full overflow-hidden rounded-full bg-muted"
      role="progressbar"
      aria-label={label}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={Math.round(clamped)}
    >
      <div
        className={cn(
          'h-full rounded-full',
          clamped >= 100 ? 'bg-destructive' : clamped >= 80 ? 'bg-warning' : 'bg-primary'
        )}
        style={{ width: `${clamped}%` }}
      />
    </div>
  )
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
      {/* Header with tier badge: the current plan is the one filled chip. */}
      <div className="flex items-center justify-between">
        <p className="label-mono">Usage</p>
        <Badge variant={usage.tier === 'free' ? 'outline' : 'default'}>{tierDisplay.name}</Badge>
      </div>

      {/* Daily usage */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">Today</span>
          <span className="font-mono tabular-nums text-foreground">
            {isDailyUnlimited ? 'Unlimited' : `${usage.daily_usage} / ${usage.daily_limit}`}
          </span>
        </div>
        {!isDailyUnlimited && <QuotaBar percent={dailyPercentUsed} label="Daily usage" />}
      </div>

      {/* Monthly usage */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">This period</span>
          <span className="font-mono tabular-nums text-foreground">
            {isMonthlyUnlimited ? 'Unlimited' : `${usage.current_usage} / ${usage.quota_limit}`}
          </span>
        </div>
        {!isMonthlyUnlimited && <QuotaBar percent={monthlyPercentUsed} label="Usage this period" />}
      </div>

      {/* Warning message */}
      {isAtLimit && (
        <div className="flex items-start gap-2 rounded-lg border border-destructive/30 bg-destructive-muted p-3">
          <ExclamationTriangleIcon aria-hidden="true" className="mt-0.5 h-5 w-5 shrink-0 text-destructive" />
          <div className="text-sm">
            <p className="font-medium text-destructive">Limit reached</p>
            <p className="text-destructive">Upgrade to continue generating content</p>
          </div>
        </div>
      )}

      {isNearLimit && !isAtLimit && (
        <div className="flex items-start gap-2 rounded-lg border border-warning/30 bg-warning-muted p-3">
          <ExclamationTriangleIcon aria-hidden="true" className="mt-0.5 h-5 w-5 shrink-0 text-warning" />
          <div className="text-sm">
            <p className="font-medium text-warning">Running low</p>
            <p className="text-warning">
              {!isDailyUnlimited
                ? `${usage.daily_remaining} generations remaining today`
                : !isMonthlyUnlimited
                ? `${usage.remaining} generations remaining this period`
                : 'Unlimited usage'}
            </p>
          </div>
        </div>
      )}

      {/* Upgrade prompt: the panel's one primary button. */}
      {showUpgradePrompt && usage.tier !== 'pro' && usage.tier !== 'business' && (
        <Link href="/pricing" className={buttonVariants({ className: 'w-full' })}>
          {usage.tier === 'free' ? 'Upgrade to Starter' : 'Upgrade to Pro'}
        </Link>
      )}

      {/* Reset time */}
      <p className="label-mono text-center normal-case tracking-normal">Resets daily at midnight UTC</p>
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
