/**
 * Types for subscription tiers and quota usage.
 *
 * Frontend tier IDs must match backend enums:
 * - apps/api/src/types/usage.py SubscriptionTier
 * - backend/src/types/payments.py SubscriptionTier
 */

export type UsageTier = 'free' | 'starter' | 'pro' | 'business'

/**
 * Usage stats returned by the quota-based usage endpoints:
 * - GET /api/v1/usage/quota/stats
 */
export interface UsageStats {
  success: boolean
  tier: UsageTier
  tier_name: string

  // Monthly/billing-period quota
  current_usage: number
  quota_limit: number
  remaining: number
  percentage_used: number
  is_quota_exceeded: boolean
  period_start: string
  reset_date: string

  // Daily quota
  daily_usage: number
  daily_limit: number
  daily_remaining: number

  // Optional (backend includes this today)
  tokens_used?: number
}

export interface UsageCheckResponse {
  success: boolean
  has_quota: boolean
  remaining: number
  daily_remaining: number
  tier: UsageTier
  quota_limit: number
  reset_date: string
}

// Tier display configuration.
//
// `color` is used both on its own (the /pricing comparison-table headers, the
// UsageIndicator icon) and paired with `bgColor` (the tier chips). Every value
// therefore carries a dark: variant, and the pairs are chosen together: the
// -700 text belongs on the -100 chip in light mode and the -300 text on the
// -900 chip in dark mode.
//
// Without the dark: variants these classes rendered dark-on-dark wherever the
// surface follows the theme. On /pricing that made the table headers 1.72:1
// (gray-700 on gray-900), 3.53:1 (amber-700) and 2.24:1 (indigo-700) — the
// "Free" header was effectively invisible. All four tiers now clear AA in
// both themes; the measured ratios are in the PR that introduced this note.
//
// NOTE: apps/web/tailwind.config.js must keep ./types/** in `content`, or
// these class names are never generated.
export const TIER_DISPLAY: Record<UsageTier, {
  name: string
  color: string
  bgColor: string
  borderColor: string
  badgeColor: string
}> = {
  free: {
    name: 'Free',
    color: 'text-gray-700 dark:text-gray-200',
    bgColor: 'bg-gray-100 dark:bg-gray-800',
    borderColor: 'border-gray-200',
    badgeColor: 'bg-gray-500',
  },
  starter: {
    name: 'Starter',
    color: 'text-amber-700 dark:text-amber-300',
    bgColor: 'bg-amber-100 dark:bg-amber-900',
    borderColor: 'border-amber-200',
    badgeColor: 'bg-amber-600',
  },
  pro: {
    name: 'Pro',
    color: 'text-indigo-700 dark:text-indigo-300',
    bgColor: 'bg-indigo-100 dark:bg-indigo-900',
    borderColor: 'border-indigo-200',
    badgeColor: 'bg-indigo-600',
  },
  business: {
    name: 'Business',
    color: 'text-purple-700 dark:text-purple-300',
    bgColor: 'bg-purple-100 dark:bg-purple-900',
    borderColor: 'border-purple-200',
    badgeColor: 'bg-purple-600',
  },
}

