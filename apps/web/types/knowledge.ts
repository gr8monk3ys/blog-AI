/**
 * Knowledge Base types.
 *
 * Mirrors backend response models from:
 * - apps/api/app/routes/knowledge.py (response models)
 * - apps/api/src/knowledge/quota.py (tier limits)
 */

export interface KBDocument {
  id: string
  filename: string
  title: string
  file_type: string
  file_size_bytes: number
  page_count?: number | null
  chunk_count: number
  status: string
  created_at: string
  metadata: Record<string, unknown>
}

export interface KBChunk {
  id: string
  chunk_index: number
  content: string
  page_number: number | null
  section_title: string | null
  token_count: number
}

export interface KBStats {
  total_documents: number
  total_chunks: number
  storage_size_bytes: number
  documents_by_type: Record<string, number>
  oldest_document?: string | null
  newest_document?: string | null
}

export interface KBTierLimits {
  tier: string
  max_documents: number | null
  max_storage_bytes: number | null
  current_documents: number
  current_storage_bytes: number
}

export interface KBStatsWithLimits extends KBStats {
  tier_limits?: KBTierLimits | null
}

export interface KBSearchResult {
  chunk_id: string
  document_id: string
  document_title: string
  content: string
  score: number
  page_number: number | null
  section_title: string | null
}

export interface KBSearchResponse {
  success: boolean
  query: string
  results: KBSearchResult[]
  total_results: number
  search_time_ms: number
}

export interface KBChunksResponse {
  success: boolean
  chunks: KBChunk[]
  total: number
}

/** File type display configuration for badges/icons. */
export const FILE_TYPE_CONFIG: Record<string, { label: string; color: string }> = {
  pdf: { label: 'PDF', color: 'text-red-500' },
  docx: { label: 'DOCX', color: 'text-blue-500' },
  doc: { label: 'DOC', color: 'text-blue-500' },
  txt: { label: 'TXT', color: 'text-gray-500' },
  md: { label: 'MD', color: 'text-green-500' },
  markdown: { label: 'MD', color: 'text-green-500' },
}

export function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`
}
