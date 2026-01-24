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
