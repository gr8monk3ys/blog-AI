/**
 * Types for social media scheduling.
 *
 * Mirrors backend responses from:
 * - /api/social/accounts/*
 * - /api/social/posts/*
 * - /api/social/campaigns/*
 */

export type SocialPlatform = 'twitter' | 'linkedin' | 'facebook' | 'instagram'

export type PostStatus =
  | 'draft'
  | 'scheduled'
  | 'publishing'
  | 'published'
  | 'failed'
  | 'cancelled'

export type CampaignStatus =
  | 'draft'
  | 'active'
  | 'paused'
  | 'completed'
  | 'cancelled'

export type RecurrenceType = 'none' | 'daily' | 'weekly' | 'monthly'

export interface PlatformConfig {
  name: string
  color: string
  bgColor: string
  maxChars: number
  icon: string
}

export const PLATFORM_CONFIG: Record<SocialPlatform, PlatformConfig> = {
  twitter: { name: 'Twitter / X', color: 'text-sky-600', bgColor: 'bg-sky-100', maxChars: 280, icon: 'X' },
  linkedin: { name: 'LinkedIn', color: 'text-blue-700', bgColor: 'bg-blue-100', maxChars: 3000, icon: 'in' },
  facebook: { name: 'Facebook', color: 'text-blue-600', bgColor: 'bg-blue-100', maxChars: 63206, icon: 'f' },
  instagram: { name: 'Instagram', color: 'text-pink-600', bgColor: 'bg-pink-100', maxChars: 2200, icon: 'ig' },
}

export interface SocialAccount {
  id: string
  platform: SocialPlatform
  platform_user_id: string
  username: string
  display_name?: string
  profile_url?: string
  avatar_url?: string
  is_active: boolean
  connected_at: string
  last_used_at?: string | null
}

export interface PostContent {
  text: string
  media?: MediaAttachment[]
  link_url?: string
  link_title?: string
  link_description?: string
  hashtags?: string[]
  mentions?: string[]
}

export interface MediaAttachment {
  url: string
  type: 'image' | 'video' | 'gif'
  alt_text?: string
}

export interface ScheduledPost {
  id: string
  account_id: string
  platform: SocialPlatform
  content: PostContent
  scheduled_at: string
  published_at?: string | null
  status: PostStatus
  recurrence: RecurrenceType
  recurrence_end_date?: string | null
  campaign_id?: string | null
  error_message?: string | null
  created_at: string
  updated_at: string
}

export interface Campaign {
  id: string
  name: string
  description?: string
  content: PostContent
  platforms: CampaignPlatformConfig[]
  status: CampaignStatus
  scheduled_at?: string | null
  recurrence: RecurrenceType
  tags?: string[]
  post_count: number
  created_at: string
  updated_at: string
}

export interface CampaignPlatformConfig {
  platform: SocialPlatform
  account_id: string
  stagger_minutes?: number
  custom_content?: Partial<PostContent>
}

export interface CampaignAnalytics {
  campaign_id: string
  campaign_name: string
  total_posts: number
  published_posts: number
  failed_posts: number
  stats: PlatformStats[]
}

export interface PlatformStats {
  platform: SocialPlatform
  impressions: number
  reach: number
  engagements: number
  clicks: number
  engagement_rate: number
}

export interface OptimalTime {
  platform: SocialPlatform
  day_of_week: string
  hour: number
  score: number
}
