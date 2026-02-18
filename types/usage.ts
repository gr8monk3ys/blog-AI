/**
 * Types for subscription tiers and quota usage.
 *
 * Frontend tier IDs must match backend enums:
 * - backend/src/types/usage.py SubscriptionTier
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

// Tier display configuration
export const TIER_DISPLAY: Record<UsageTier, {
  name: string
  color: string
  bgColor: string
  borderColor: string
  badgeColor: string
}> = {
  free: {
    name: 'Free',
    color: 'text-gray-700',
    bgColor: 'bg-gray-100',
    borderColor: 'border-gray-200',
    badgeColor: 'bg-gray-500',
  },
  starter: {
    name: 'Starter',
    color: 'text-amber-700',
    bgColor: 'bg-amber-100',
    borderColor: 'border-amber-200',
    badgeColor: 'bg-amber-600',
  },
  pro: {
    name: 'Pro',
    color: 'text-indigo-700',
    bgColor: 'bg-indigo-100',
    borderColor: 'border-indigo-200',
    badgeColor: 'bg-indigo-600',
  },
  business: {
    name: 'Business',
    color: 'text-purple-700',
    bgColor: 'bg-purple-100',
    borderColor: 'border-purple-200',
    badgeColor: 'bg-purple-600',
  },
}

