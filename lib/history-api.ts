/**
 * History API client for Blog-AI
 *
 * Provides methods for managing content history and favorites.
 * Uses Supabase for data storage.
 */

import { createClient } from '@supabase/supabase-js'
import { isSupabaseConfigured } from './supabase'
import type {
  GeneratedContentItem,
  HistoryFilters,
  HistoryResponse,
  HistoryStats,
  SaveContentInput,
} from '../types/history'
import type { ToolCategory } from '../types/tools'

/**
 * Get a lightweight Supabase client without strict database types
 * This avoids type conflicts while still providing runtime functionality
 */
function getHistoryClient() {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

  if (!supabaseUrl || !supabaseAnonKey) {
    return null
  }

  return createClient(supabaseUrl, supabaseAnonKey)
}

/**
 * Generate a consistent user hash for anonymous tracking
 * Uses a combination of browser fingerprint data
 */
function generateUserHash(): string {
  if (typeof window === 'undefined') return ''

  const data = [
    navigator.userAgent,
    navigator.language,
    screen.width,
    screen.height,
    new Date().getTimezoneOffset(),
  ].join('|')

  // Simple hash function
  let hash = 0
  for (let i = 0; i < data.length; i++) {
    const char = data.charCodeAt(i)
    hash = ((hash << 5) - hash) + char
    hash = hash & hash
  }
  return `user_${Math.abs(hash).toString(16)}`
}

/**
 * Get cached user hash or generate new one
 */
function getUserHash(): string {
  if (typeof window === 'undefined') return ''

  const storageKey = 'blog_ai_user_hash'
  let hash = localStorage.getItem(storageKey)

  if (!hash) {
    hash = generateUserHash()
    localStorage.setItem(storageKey, hash)
  }

  return hash
}

/**
 * Map tool_id to category (for filtering)
 */
function getToolCategory(toolId: string): ToolCategory | null {
  const categoryMap: Record<string, ToolCategory> = {
    'blog-post-generator': 'blog',
    'blog-outline': 'blog',
    'blog-intro-generator': 'blog',
    'blog-conclusion': 'blog',
    'email-subject-lines': 'email',
    'cold-email-generator': 'email',
    'newsletter-writer': 'email',
    'follow-up-email': 'email',
    'instagram-caption': 'social-media',
    'twitter-thread': 'social-media',
    'linkedin-post': 'social-media',
    'facebook-ad-copy': 'social-media',
    'business-plan': 'business',
    'product-description': 'business',
    'press-release': 'business',
    'proposal-writer': 'business',
    'brand-name-generator': 'naming',
    'tagline-generator': 'naming',
    'domain-name-ideas': 'naming',
    'youtube-title': 'video',
    'video-script': 'video',
    'youtube-description': 'video',
    'meta-description': 'seo',
    'keyword-research': 'seo',
    'seo-title': 'seo',
    'content-rewriter': 'rewriting',
    'sentence-rewriter': 'rewriting',
    'tone-changer': 'rewriting',
    'grammar-improver': 'rewriting',
  }
  return categoryMap[toolId] || null
}

/**
 * History API methods
 */
export const historyApi = {
  /**
   * Check if history features are available
   */
  isAvailable(): boolean {
    return isSupabaseConfigured()
  },

  /**
   * Get content history with optional filters
   */
  async getHistory(filters: HistoryFilters = {}): Promise<HistoryResponse> {
    const supabase = getHistoryClient()
    if (!supabase) {
      return { items: [], total: 0, limit: 20, offset: 0, has_more: false }
    }

    const userHash = getUserHash()
    const limit = filters.limit || 20
    const offset = filters.offset || 0

    let query = supabase
      .from('generated_content')
      .select('*', { count: 'exact' })
      .eq('user_hash', userHash)
      .order('created_at', { ascending: false })

    // Apply filters
    if (filters.favorites_only) {
      query = query.eq('is_favorite', true)
    }

    if (filters.tool_id) {
      query = query.eq('tool_id', filters.tool_id)
    }

    if (filters.date_from) {
      query = query.gte('created_at', filters.date_from)
    }

    if (filters.date_to) {
      query = query.lte('created_at', filters.date_to)
    }

    if (filters.search) {
      // Search in title, output, and inputs
      query = query.or(
        `title.ilike.%${filters.search}%,output.ilike.%${filters.search}%`
      )
    }

    // Apply pagination
    query = query.range(offset, offset + limit - 1)

    const { data, error, count } = await query

    if (error) {
      console.error('Error fetching history:', error)
      throw new Error('Failed to fetch history')
    }

    // Filter by category client-side if needed
    let items = (data || []) as GeneratedContentItem[]
    if (filters.category && filters.category !== 'all') {
      items = items.filter((item) => getToolCategory(item.tool_id) === filters.category)
    }

    return {
      items,
      total: count || 0,
      limit,
      offset,
      has_more: (count || 0) > offset + limit,
    }
  },

  /**
   * Get a single history item by ID
   */
  async getById(id: string): Promise<GeneratedContentItem | null> {
    const supabase = getHistoryClient()
    if (!supabase) return null

    const { data, error } = await supabase
      .from('generated_content')
      .select('*')
      .eq('id', id)
      .single()

    if (error) {
      if (error.code === 'PGRST116') return null
      console.error('Error fetching content:', error)
      throw new Error('Failed to fetch content')
    }

    return data as GeneratedContentItem
  },

  /**
   * Toggle favorite status of a content item
   */
  async toggleFavorite(id: string): Promise<boolean> {
    const supabase = getHistoryClient()
    if (!supabase) {
      throw new Error('Supabase not configured')
    }

    // Use direct update instead of RPC for better type safety
    const { data: current, error: fetchError } = await supabase
      .from('generated_content')
      .select('is_favorite')
      .eq('id', id)
      .single()

    if (fetchError) {
      console.error('Error fetching content:', fetchError)
      throw new Error('Failed to fetch content for toggle')
    }

    const currentRow = current as { is_favorite?: boolean } | null
    const newStatus = !(currentRow?.is_favorite ?? false)

    const { error: updateError } = await supabase
      .from('generated_content')
      .update({ is_favorite: newStatus })
      .eq('id', id)

    if (updateError) {
      console.error('Error toggling favorite:', updateError)
      throw new Error('Failed to toggle favorite')
    }

    return newStatus
  },

  /**
   * Set favorite status explicitly
   */
  async setFavorite(id: string, isFavorite: boolean): Promise<boolean> {
    const supabase = getHistoryClient()
    if (!supabase) {
      throw new Error('Supabase not configured')
    }

    const { error } = await supabase
      .from('generated_content')
      .update({ is_favorite: isFavorite })
      .eq('id', id)

    if (error) {
      console.error('Error setting favorite:', error)
      throw new Error('Failed to set favorite')
    }

    return isFavorite
  },

  /**
   * Delete a generated content item
   */
  async deleteGeneration(id: string): Promise<void> {
    const supabase = getHistoryClient()
    if (!supabase) {
      throw new Error('Supabase not configured')
    }

    const userHash = getUserHash()

    const { error } = await supabase
      .from('generated_content')
      .delete()
      .eq('id', id)
      .eq('user_hash', userHash)

    if (error) {
      console.error('Error deleting content:', error)
      throw new Error('Failed to delete content')
    }
  },

  /**
   * Save generated content to history
   */
  async saveGeneration(input: SaveContentInput): Promise<GeneratedContentItem> {
    const supabase = getHistoryClient()
    if (!supabase) {
      throw new Error('Supabase not configured')
    }

    const userHash = getUserHash()

    const insertData = {
      tool_id: input.tool_id,
      tool_name: input.tool_name,
      title: input.title || null,
      inputs: input.inputs,
      output: input.output,
      provider: input.provider,
      execution_time_ms: input.execution_time_ms,
      user_hash: userHash,
      is_favorite: false,
    }

    const { data, error } = await supabase
      .from('generated_content')
      .insert(insertData)
      .select()
      .single()

    if (error) {
      console.error('Error saving content:', error)
      throw new Error('Failed to save content')
    }

    return data as GeneratedContentItem
  },

  /**
   * Get history statistics
   */
  async getStats(): Promise<HistoryStats> {
    const supabase = getHistoryClient()
    if (!supabase) {
      return {
        total_generations: 0,
        total_favorites: 0,
        by_category: {},
        by_tool: {},
        recent_count: 0,
      }
    }

    const userHash = getUserHash()
    const sevenDaysAgo = new Date()
    sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7)

    // Get total count
    const { count: totalCount } = await supabase
      .from('generated_content')
      .select('*', { count: 'exact', head: true })
      .eq('user_hash', userHash)

    // Get favorites count
    const { count: favoritesCount } = await supabase
      .from('generated_content')
      .select('*', { count: 'exact', head: true })
      .eq('user_hash', userHash)
      .eq('is_favorite', true)

    // Get recent count
    const { count: recentCount } = await supabase
      .from('generated_content')
      .select('*', { count: 'exact', head: true })
      .eq('user_hash', userHash)
      .gte('created_at', sevenDaysAgo.toISOString())

    // Get all items for category/tool breakdown
    const { data: allItems } = await supabase
      .from('generated_content')
      .select('tool_id')
      .eq('user_hash', userHash)

    const byCategory: Record<string, number> = {}
    const byTool: Record<string, number> = {}

    if (allItems) {
      for (const item of allItems as { tool_id: string }[]) {
        const category = getToolCategory(item.tool_id)
        if (category) {
          byCategory[category] = (byCategory[category] || 0) + 1
        }
        byTool[item.tool_id] = (byTool[item.tool_id] || 0) + 1
      }
    }

    return {
      total_generations: totalCount || 0,
      total_favorites: favoritesCount || 0,
      by_category: byCategory,
      by_tool: byTool,
      recent_count: recentCount || 0,
    }
  },

  /**
   * Get favorites only
   */
  async getFavorites(limit = 20, offset = 0): Promise<HistoryResponse> {
    return this.getHistory({ favorites_only: true, limit, offset })
  },
}

export default historyApi
