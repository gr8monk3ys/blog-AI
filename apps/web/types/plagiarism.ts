/**
 * Types for plagiarism / originality checks.
 *
 * Mirrors backend responses from:
 * - POST /api/v1/content/check-plagiarism
 */

export type PlagiarismProvider = 'copyscape' | 'originality' | 'embedding'

export type PlagiarismCheckStatus =
  | 'pending'
  | 'in_progress'
  | 'completed'
  | 'failed'
  | 'cached'

export type PlagiarismRiskLevel =
  | 'none'
  | 'low'
  | 'moderate'
  | 'high'
  | 'critical'

export interface MatchingSource {
  url: string
  title?: string | null
  similarity_percentage: number
  matched_words: number
  matched_text?: string | null
  is_exact_match: boolean
}

export interface PlagiarismCheckResult {
  check_id: string
  status: PlagiarismCheckStatus
  provider: PlagiarismProvider
  overall_score: number
  risk_level: PlagiarismRiskLevel
  original_percentage: number
  matching_sources: MatchingSource[]
  total_words_checked: number
  total_matched_words: number
  check_timestamp: string
  cached: boolean
  cache_key?: string | null
  api_credits_used: number
  error_message?: string | null
  processing_time_ms: number
  metadata: Record<string, unknown>
}

export interface PlagiarismCheckResponse {
  success: boolean
  data?: PlagiarismCheckResult | null
  error?: string | null
}

