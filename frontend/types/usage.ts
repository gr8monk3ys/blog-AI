/**
 * Types for usage tracking and tier management
 */

export type UsageTier = 'free' | 'pro' | 'enterprise'

export interface UsageStats {
  user_hash: string
  tier: UsageTier
  daily_count: number
  daily_limit: number
  daily_remaining: number
  monthly_count: number
  monthly_limit: number
  monthly_remaining: number
  tokens_used_today: number
  tokens_used_month: number
  is_limit_reached: boolean
  percentage_used_daily: number
  percentage_used_monthly: number
  reset_daily_at: string
  reset_monthly_at: string
}

export interface TierInfo {
  name: string
  daily_limit: number
  monthly_limit: number
  features_enabled: string[]
  price_monthly: number
  price_yearly: number
  description: string
}

export interface AllTiersResponse {
  tiers: TierInfo[]
  current_tier: UsageTier
}

export interface UsageCheckResponse {
  success: boolean
  can_generate: boolean
  remaining_today: number
  tier: UsageTier
  daily_limit: number
  monthly_remaining: number
}

export interface UsageLimitError {
  success: false
  error: string
  tier: UsageTier
  limit_type: 'daily' | 'monthly'
  upgrade_url: string
  daily_limit: number
  daily_remaining: number
  monthly_limit: number
  monthly_remaining: number
}

export interface UserFeatures {
  tier: UsageTier
  tier_name: string
  features_enabled: string[]
  bulk_generation_enabled: boolean
  research_enabled: boolean
  api_access_enabled: boolean
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
  pro: {
    name: 'Pro',
    color: 'text-indigo-700',
    bgColor: 'bg-indigo-100',
    borderColor: 'border-indigo-200',
    badgeColor: 'bg-indigo-500',
  },
  enterprise: {
    name: 'Enterprise',
    color: 'text-purple-700',
    bgColor: 'bg-purple-100',
    borderColor: 'border-purple-200',
    badgeColor: 'bg-purple-500',
  },
}
