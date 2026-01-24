/**
 * Types for content history and favorites
 */

import type { ToolCategory } from './tools'

/**
 * Generated content item from the database
 */
export interface GeneratedContentItem {
  id: string
  created_at: string
  updated_at: string
  tool_id: string
  tool_name: string | null
  title: string | null
  inputs: Record<string, unknown>
  output: string
  provider: string
  execution_time_ms: number
  user_hash: string | null
  is_favorite: boolean
}

/**
 * Filters for querying history
 */
export interface HistoryFilters {
  category?: ToolCategory | 'all'
  search?: string
  favorites_only?: boolean
  date_from?: string
  date_to?: string
  tool_id?: string
  limit?: number
  offset?: number
}

/**
 * Paginated history response
 */
export interface HistoryResponse {
  items: GeneratedContentItem[]
  total: number
  limit: number
  offset: number
  has_more: boolean
}

/**
 * History statistics
 */
export interface HistoryStats {
  total_generations: number
  total_favorites: number
  by_category: Record<string, number>
  by_tool: Record<string, number>
  recent_count: number
}

/**
 * Input for saving generated content
 */
export interface SaveContentInput {
  tool_id: string
  tool_name: string
  title?: string
  inputs: Record<string, unknown>
  output: string
  provider: string
  execution_time_ms: number
}
