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
// A tier is a word, not a colour (DESIGN.md → Colors → The One Pen Rule): the
// four plans used to be grey, amber, indigo and purple, and every consumer
// now sets the name as a wall label or the house chip, with the ink-filled
// chip reserved for the plan the account is on. The class fields are kept so
// the call sites keep compiling, and all four tiers resolve to the same
// paper-card tokens; `badgeColor` is the dot beside a plan name.
//
// NOTE: apps/web/app/globals.css must keep `@source '../types'`, or these
// class names are never generated.
export const TIER_DISPLAY: Record<UsageTier, {
  name: string
  color: string
  bgColor: string
  /** The /knowledge plan badge wash. */
  planBgColor: string
  borderColor: string
  badgeColor: string
}> = {
  free: {
    name: 'Free',
    color: 'text-foreground',
    bgColor: 'bg-card',
    planBgColor: 'bg-card',
    borderColor: 'border-border',
    badgeColor: 'bg-muted-foreground',
  },
  starter: {
    name: 'Starter',
    color: 'text-foreground',
    bgColor: 'bg-card',
    planBgColor: 'bg-card',
    borderColor: 'border-border',
    badgeColor: 'bg-muted-foreground',
  },
  pro: {
    name: 'Pro',
    color: 'text-foreground',
    bgColor: 'bg-card',
    planBgColor: 'bg-card',
    borderColor: 'border-border',
    badgeColor: 'bg-primary',
  },
  business: {
    name: 'Business',
    color: 'text-foreground',
    bgColor: 'bg-card',
    planBgColor: 'bg-card',
    borderColor: 'border-border',
    badgeColor: 'bg-primary',
  },
}
