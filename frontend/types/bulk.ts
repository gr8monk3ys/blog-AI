/**
 * Types for bulk generation
 */

import { BlogContent } from './content'

export interface BulkGenerationItem {
  topic: string
  keywords: string[]
  tone: string
}

export interface BulkGenerationRequest {
  items: BulkGenerationItem[]
  tool_id: string
  research: boolean
  proofread: boolean
  humanize: boolean
  parallel_limit: number
  conversation_id: string
}

export interface BulkGenerationItemResult {
  index: number
  success: boolean
  topic: string
  content?: BlogContent
  error?: string
  execution_time_ms: number
}

export interface BulkGenerationResponse {
  success: boolean
  job_id: string
  total_items: number
  completed_items: number
  failed_items: number
  results: BulkGenerationItemResult[]
  total_execution_time_ms: number
  message?: string
}

export interface BulkGenerationStatus {
  job_id: string
  status: 'pending' | 'processing' | 'completed' | 'cancelled' | 'failed'
  total_items: number
  completed_items: number
  failed_items: number
  progress_percentage: number
  started_at?: string
  completed_at?: string
  can_cancel: boolean
}

export interface BulkJobStartResponse {
  success: boolean
  job_id: string
  status: string
  total_items: number
  message: string
}

export interface BulkProgressUpdate {
  type: 'bulk_progress'
  job_id: string
  completed: number
  total: number
  latest_result: {
    index: number
    success: boolean
    topic: string
  }
}

export interface BulkCompletedUpdate {
  type: 'bulk_completed'
  job_id: string
  completed: number
  failed: number
  total: number
}

// CSV parsing types
export interface CSVRow {
  topic: string
  keywords?: string
  tone?: string
}

export interface ParsedCSVData {
  rows: CSVRow[]
  errors: string[]
  headers: string[]
}

// ============================================================================
// Enhanced Tier 1 Types
// ============================================================================

export type ProviderStrategy = 'single' | 'round_robin' | 'load_balanced' | 'cost_optimized' | 'quality_optimized'

export type ExportFormat = 'json' | 'csv' | 'markdown' | 'zip'

export interface CostEstimate {
  estimated_input_tokens: number
  estimated_output_tokens: number
  estimated_cost_usd: number
  cost_breakdown: Record<string, number>
  confidence: number
  provider_recommendations: ProviderRecommendation[]
}

export interface ProviderRecommendation {
  provider: string
  display_name: string
  estimated_cost: number
  input_cost: number
  output_cost: number
}

export interface EnhancedBatchRequest {
  items: BulkGenerationItem[]
  provider_strategy: ProviderStrategy
  preferred_provider: string
  fallback_providers: string[]
  parallel_limit: number
  research_enabled: boolean
  proofread_enabled: boolean
  humanize_enabled: boolean
  brand_profile_id?: string
  name?: string
  tags?: string[]
  conversation_id: string
}

export interface EnhancedBatchStatus extends BulkGenerationStatus {
  name?: string
  provider_strategy: ProviderStrategy
  providers_used: Record<string, number>
  estimated_cost_usd: number
  actual_cost_usd: number
  total_tokens_used: number
  can_retry_failed: boolean
}

export interface EnhancedBatchItemResult extends BulkGenerationItemResult {
  item_id: string
  status: 'pending' | 'queued' | 'processing' | 'completed' | 'failed' | 'cancelled' | 'partial'
  provider_used?: string
  token_count: number
  cost_usd: number
  retry_count: number
  started_at?: string
  completed_at?: string
}

export interface RetryRequest {
  item_indices?: number[]
  change_provider?: string
}

export interface BatchJobListResponse {
  jobs: EnhancedBatchStatus[]
  total: number
  limit: number
  offset: number
  has_more: boolean
}
