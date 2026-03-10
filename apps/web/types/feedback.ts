/**
 * Types for the content feedback and rating system
 */

export const FEEDBACK_TAGS = [
  'Too formal',
  'Too casual',
  'Good length',
  'Too long',
  'Too short',
  'Sounds AI-generated',
  'Sounds natural',
  'Off-topic',
  'Great quality',
] as const

export type FeedbackTag = (typeof FEEDBACK_TAGS)[number]

export interface FeedbackSubmission {
  content_id: string
  rating: number
  tags: FeedbackTag[]
  feedback_text?: string
}

export interface FeedbackResponse {
  success: boolean
  data?: {
    id: string
    created_at: string
  }
  error?: string
}

export interface FeedbackTagStat {
  tag: FeedbackTag
  count: number
}

export interface FeedbackStats {
  content_id: string
  average_rating: number
  total_ratings: number
  rating_distribution: Record<number, number>
  common_tags: FeedbackTagStat[]
}

export interface FeedbackStatsResponse {
  success: boolean
  data?: FeedbackStats
  error?: string
}
