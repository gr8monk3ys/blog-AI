/**
 * History API client for Blog-AI
 *
 * Talks to same-origin Next.js route handlers which persist to Neon.
 * Requires an authenticated Clerk session for persistence.
 */

import type {
  GeneratedContentItem,
  HistoryFilters,
  HistoryResponse,
  HistoryStats,
  SaveContentInput,
} from '../types/history'
import type { ToolCategory } from '../types/tools'

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

async function jsonOrThrow<T>(res: Response): Promise<T> {
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    const message =
      (data && typeof data === 'object' && 'error' in data && typeof data.error === 'string'
        ? data.error
        : `Request failed (${res.status})`)
    const error = new Error(message)
    ;(error as any).status = res.status
    throw error
  }
  return data as T
}

export const historyApi = {
  isAvailable(): boolean {
    // Availability is determined by auth + server configuration; handle per-request errors.
    return true
  },

  async getHistory(filters: HistoryFilters = {}): Promise<HistoryResponse> {
    const params = new URLSearchParams()
    if (filters.favorites_only) params.set('favorites_only', 'true')
    if (filters.tool_id) params.set('tool_id', filters.tool_id)
    if (filters.date_from) params.set('date_from', filters.date_from)
    if (filters.date_to) params.set('date_to', filters.date_to)
    if (filters.search) params.set('search', filters.search)
    params.set('limit', String(filters.limit ?? 20))
    params.set('offset', String(filters.offset ?? 0))

    try {
      const res = await fetch(`/api/history?${params.toString()}`, {
        method: 'GET',
        headers: { Accept: 'application/json' },
      })
      const payload = await jsonOrThrow<HistoryResponse & { items: GeneratedContentItem[] }>(res)

      // Optional category filtering is done client-side (tool_id -> category).
      let items = payload.items || []
      if (filters.category && filters.category !== 'all') {
        items = items.filter((item) => getToolCategory(item.tool_id) === filters.category)
      }

      return {
        ...payload,
        items,
      }
    } catch (e: any) {
      // If not signed in or history is unavailable, behave like "no history".
      if (e?.status === 401 || e?.status === 403 || e?.status === 503) {
        return { items: [], total: 0, limit: filters.limit ?? 20, offset: filters.offset ?? 0, has_more: false }
      }
      throw e
    }
  },

  async getById(id: string): Promise<GeneratedContentItem | null> {
    const res = await fetch(`/api/history/${encodeURIComponent(id)}`, {
      method: 'GET',
      headers: { Accept: 'application/json' },
    })

    if (res.status === 404) return null
    if (res.status === 401 || res.status === 403 || res.status === 503) return null

    const payload = await jsonOrThrow<{ data: GeneratedContentItem }>(res)
    return payload.data
  },

  async toggleFavorite(id: string): Promise<boolean> {
    const res = await fetch(`/api/history/${encodeURIComponent(id)}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify({ toggle: true }),
    })
    const payload = await jsonOrThrow<{ is_favorite: boolean }>(res)
    return payload.is_favorite
  },

  async setFavorite(id: string, isFavorite: boolean): Promise<boolean> {
    const res = await fetch(`/api/history/${encodeURIComponent(id)}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify({ isFavorite }),
    })
    const payload = await jsonOrThrow<{ is_favorite: boolean }>(res)
    return payload.is_favorite
  },

  async deleteGeneration(id: string): Promise<void> {
    const res = await fetch(`/api/history/${encodeURIComponent(id)}`, {
      method: 'DELETE',
      headers: { Accept: 'application/json' },
    })
    if (res.status === 404) return
    await jsonOrThrow(res)
  },

  async saveGeneration(input: SaveContentInput): Promise<GeneratedContentItem> {
    const res = await fetch('/api/history', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify(input),
    })
    const payload = await jsonOrThrow<{ data: GeneratedContentItem }>(res)
    return payload.data
  },

  async getStats(): Promise<HistoryStats> {
    try {
      const res = await fetch('/api/history/stats', {
        method: 'GET',
        headers: { Accept: 'application/json' },
      })
      const payload = await jsonOrThrow<HistoryStats>(res)

      // If server returns empty by_category, compute from by_tool.
      if (!payload.by_category || Object.keys(payload.by_category).length === 0) {
        const byCategory: Record<string, number> = {}
        for (const [toolId, count] of Object.entries(payload.by_tool || {})) {
          const category = getToolCategory(toolId)
          if (!category) continue
          byCategory[category] = (byCategory[category] || 0) + count
        }
        return { ...payload, by_category: byCategory }
      }

      return payload
    } catch (e: any) {
      if (e?.status === 401 || e?.status === 403 || e?.status === 503) {
        return {
          total_generations: 0,
          total_favorites: 0,
          by_category: {},
          by_tool: {},
          recent_count: 0,
        }
      }
      throw e
    }
  },

  async getFavorites(limit = 20, offset = 0): Promise<HistoryResponse> {
    return this.getHistory({ favorites_only: true, limit, offset })
  },
}

export default historyApi

