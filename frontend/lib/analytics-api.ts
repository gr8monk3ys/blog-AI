/**
 * Analytics API client for Blog-AI
 *
 * Provides methods for fetching analytics data from the backend.
 * Falls back to Supabase direct queries when backend is unavailable.
 */

import { API_BASE_URL, API_VERSION, apiFetch } from './api'
import { getSupabase, isSupabaseConfigured } from './supabase'
import type {
  OverviewStats,
  ToolUsageStat,
  TimelineDataPoint,
  CategoryBreakdown,
  TimeRangeOption,
} from '../types/analytics'
import { CATEGORY_COLORS } from '../types/analytics'

// API endpoint base
const ANALYTICS_API_BASE = `${API_BASE_URL}/api/${API_VERSION}/analytics`

/**
 * Analytics API response types
 */
interface AnalyticsOverviewResponse {
  total_generations: number
  total_tools_used: number
  active_today: number
  average_execution_time_ms: number
  popular_tool: string | null
  generations_change_percent: number
}

interface ToolUsageResponse {
  tool_id: string
  tool_name: string
  category: string
  count: number
  last_used_at: string
  percentage: number
}

interface TimelineResponse {
  date: string
  count: number
}

interface CategoryResponse {
  category: string
  count: number
  percentage: number
}

/**
 * Get overview statistics
 */
export async function getOverviewStats(
  timeRange: TimeRangeOption = '30d'
): Promise<OverviewStats> {
  try {
    const response = await apiFetch<AnalyticsOverviewResponse>(
      `${ANALYTICS_API_BASE}/overview?range=${timeRange}`
    )

    return {
      totalGenerations: response.total_generations,
      totalToolsUsed: response.total_tools_used,
      activeToday: response.active_today,
      averageExecutionTime: response.average_execution_time_ms,
      popularTool: response.popular_tool,
      generationsChange: response.generations_change_percent,
    }
  } catch {
    // Fall back to Supabase direct query
    return getOverviewStatsFromSupabase(timeRange)
  }
}

/**
 * Get tool usage statistics
 */
export async function getToolUsageStats(
  timeRange: TimeRangeOption = '30d',
  limit = 10
): Promise<ToolUsageStat[]> {
  try {
    const response = await apiFetch<ToolUsageResponse[]>(
      `${ANALYTICS_API_BASE}/tools?range=${timeRange}&limit=${limit}`
    )

    return response.map((item) => ({
      toolId: item.tool_id,
      toolName: item.tool_name,
      category: item.category,
      count: item.count,
      lastUsedAt: item.last_used_at,
      percentage: item.percentage,
    }))
  } catch {
    // Fall back to Supabase direct query
    return getToolUsageFromSupabase(timeRange, limit)
  }
}

/**
 * Get timeline data for generations over time
 */
export async function getTimelineData(
  timeRange: TimeRangeOption = '30d'
): Promise<TimelineDataPoint[]> {
  try {
    const response = await apiFetch<TimelineResponse[]>(
      `${ANALYTICS_API_BASE}/timeline?range=${timeRange}`
    )

    return response.map((item) => ({
      date: item.date,
      count: item.count,
      label: formatDateLabel(item.date, timeRange),
    }))
  } catch {
    // Fall back to Supabase direct query
    return getTimelineFromSupabase(timeRange)
  }
}

/**
 * Get category breakdown
 */
export async function getCategoryBreakdown(
  timeRange: TimeRangeOption = '30d'
): Promise<CategoryBreakdown[]> {
  try {
    const response = await apiFetch<CategoryResponse[]>(
      `${ANALYTICS_API_BASE}/categories?range=${timeRange}`
    )

    return response.map((item) => ({
      category: item.category,
      count: item.count,
      percentage: item.percentage,
      color: CATEGORY_COLORS[item.category] || '#6b7280',
    }))
  } catch {
    // Fall back to Supabase direct query
    return getCategoryBreakdownFromSupabase(timeRange)
  }
}

// =============================================================================
// Supabase Fallback Functions
// =============================================================================

// Internal types for Supabase responses
interface GeneratedContentRow {
  execution_time_ms: number
  created_at: string
  tool_id: string
}

interface ToolUsageRow {
  tool_id: string
  count: number
  last_used_at: string
}

async function getOverviewStatsFromSupabase(
  timeRange: TimeRangeOption
): Promise<OverviewStats> {
  if (!isSupabaseConfigured()) {
    return getMockOverviewStats()
  }

  try {
    const supabase = getSupabase()
    const { start, end } = getTimeRangeDates(timeRange)
    const today = new Date().toISOString().split('T')[0]

    // Get total generations in range
    const genResult = await supabase
      .from('generated_content')
      .select('*', { count: 'exact', head: true })
      .gte('created_at', start)
      .lte('created_at', end)

    const totalGenerations = genResult.count || 0

    // Get unique tools used
    const toolResult = await supabase
      .from('tool_usage')
      .select('tool_id')

    const totalToolsUsed = toolResult.data?.length || 0

    // Get today's activity
    const todayResult = await supabase
      .from('generated_content')
      .select('*', { count: 'exact', head: true })
      .gte('created_at', today)

    const activeToday = todayResult.count || 0

    // Get average execution time
    const execResult = await supabase
      .from('generated_content')
      .select('execution_time_ms')
      .gte('created_at', start)
      .lte('created_at', end)

    const execData = (execResult.data || []) as unknown as GeneratedContentRow[]
    const avgExecTime = execData.length
      ? execData.reduce((sum, r) => sum + (r.execution_time_ms || 0), 0) / execData.length
      : 0

    // Get most popular tool
    const popularResult = await supabase
      .from('tool_usage')
      .select('tool_id, count')
      .order('count', { ascending: false })
      .limit(1)
      .single()

    const popularToolData = popularResult.data as unknown as ToolUsageRow | null

    return {
      totalGenerations,
      totalToolsUsed,
      activeToday,
      averageExecutionTime: Math.round(avgExecTime),
      popularTool: popularToolData?.tool_id || null,
      generationsChange: 0, // Would need previous period comparison
    }
  } catch {
    return getMockOverviewStats()
  }
}

async function getToolUsageFromSupabase(
  timeRange: TimeRangeOption,
  limit: number
): Promise<ToolUsageStat[]> {
  if (!isSupabaseConfigured()) {
    return getMockToolUsageStats()
  }

  try {
    const supabase = getSupabase()

    const result = await supabase
      .from('tool_usage')
      .select('*')
      .order('count', { ascending: false })
      .limit(limit)

    if (result.error || !result.data) {
      return getMockToolUsageStats()
    }

    const data = result.data as unknown as ToolUsageRow[]
    const totalCount = data.reduce((sum, item) => sum + (item.count || 0), 0)

    return data.map((item) => ({
      toolId: item.tool_id,
      toolName: formatToolName(item.tool_id),
      category: extractCategory(item.tool_id),
      count: item.count || 0,
      lastUsedAt: item.last_used_at,
      percentage: totalCount > 0 ? ((item.count || 0) / totalCount) * 100 : 0,
    }))
  } catch {
    return getMockToolUsageStats()
  }
}

async function getTimelineFromSupabase(
  timeRange: TimeRangeOption
): Promise<TimelineDataPoint[]> {
  if (!isSupabaseConfigured()) {
    return getMockTimelineData(timeRange)
  }

  try {
    const supabase = getSupabase()
    const { start, end } = getTimeRangeDates(timeRange)

    const result = await supabase
      .from('generated_content')
      .select('created_at')
      .gte('created_at', start)
      .lte('created_at', end)
      .order('created_at', { ascending: true })

    if (result.error || !result.data) {
      return getMockTimelineData(timeRange)
    }

    const data = result.data as unknown as { created_at: string }[]

    // Group by date
    const grouped: Record<string, number> = {}
    data.forEach((item) => {
      const date = item.created_at.split('T')[0]
      grouped[date] = (grouped[date] || 0) + 1
    })

    return Object.entries(grouped).map(([date, count]) => ({
      date,
      count,
      label: formatDateLabel(date, timeRange),
    }))
  } catch {
    return getMockTimelineData(timeRange)
  }
}

async function getCategoryBreakdownFromSupabase(
  timeRange: TimeRangeOption
): Promise<CategoryBreakdown[]> {
  if (!isSupabaseConfigured()) {
    return getMockCategoryBreakdown()
  }

  try {
    const supabase = getSupabase()
    const { start, end } = getTimeRangeDates(timeRange)

    const result = await supabase
      .from('generated_content')
      .select('tool_id')
      .gte('created_at', start)
      .lte('created_at', end)

    if (result.error || !result.data) {
      return getMockCategoryBreakdown()
    }

    const data = result.data as unknown as { tool_id: string }[]

    // Group by category
    const grouped: Record<string, number> = {}
    data.forEach((item) => {
      const category = extractCategory(item.tool_id)
      grouped[category] = (grouped[category] || 0) + 1
    })

    const total = Object.values(grouped).reduce((sum, count) => sum + count, 0)

    return Object.entries(grouped).map(([category, count]) => ({
      category,
      count,
      percentage: total > 0 ? (count / total) * 100 : 0,
      color: CATEGORY_COLORS[category] || '#6b7280',
    }))
  } catch {
    return getMockCategoryBreakdown()
  }
}

// =============================================================================
// Helper Functions
// =============================================================================

function getTimeRangeDates(timeRange: TimeRangeOption): { start: string; end: string } {
  const now = new Date()
  let start: Date

  switch (timeRange) {
    case '7d':
      start = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
      break
    case '30d':
      start = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
      break
    case '90d':
      start = new Date(now.getTime() - 90 * 24 * 60 * 60 * 1000)
      break
    case 'all':
    default:
      start = new Date(0)
  }

  return {
    start: start.toISOString(),
    end: now.toISOString(),
  }
}

function formatToolName(toolId: string): string {
  return toolId
    .split('-')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

function extractCategory(toolId: string): string {
  // Common patterns: blog-post-generator, email-subject-lines, etc.
  const categoryMap: Record<string, string> = {
    blog: 'blog',
    email: 'email',
    newsletter: 'email',
    instagram: 'social-media',
    twitter: 'social-media',
    linkedin: 'social-media',
    facebook: 'social-media',
    social: 'social-media',
    business: 'business',
    product: 'business',
    brand: 'naming',
    tagline: 'naming',
    domain: 'naming',
    youtube: 'video',
    video: 'video',
    meta: 'seo',
    seo: 'seo',
    keyword: 'seo',
    rewrite: 'rewriting',
    sentence: 'rewriting',
    tone: 'rewriting',
    grammar: 'rewriting',
  }

  const lowerToolId = toolId.toLowerCase()
  for (const [key, category] of Object.entries(categoryMap)) {
    if (lowerToolId.includes(key)) {
      return category
    }
  }

  return 'blog' // Default category
}

function formatDateLabel(date: string, timeRange: TimeRangeOption): string {
  const d = new Date(date)
  if (timeRange === '7d') {
    return d.toLocaleDateString('en-US', { weekday: 'short' })
  }
  if (timeRange === '30d') {
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  }
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

// =============================================================================
// Mock Data (for development/demo)
// =============================================================================

function getMockOverviewStats(): OverviewStats {
  return {
    totalGenerations: 1247,
    totalToolsUsed: 18,
    activeToday: 42,
    averageExecutionTime: 2340,
    popularTool: 'blog-post-generator',
    generationsChange: 12.5,
  }
}

function getMockToolUsageStats(): ToolUsageStat[] {
  return [
    {
      toolId: 'blog-post-generator',
      toolName: 'Blog Post Generator',
      category: 'blog',
      count: 324,
      lastUsedAt: new Date().toISOString(),
      percentage: 26,
    },
    {
      toolId: 'email-subject-lines',
      toolName: 'Email Subject Lines',
      category: 'email',
      count: 218,
      lastUsedAt: new Date().toISOString(),
      percentage: 17.5,
    },
    {
      toolId: 'instagram-caption',
      toolName: 'Instagram Caption',
      category: 'social-media',
      count: 186,
      lastUsedAt: new Date().toISOString(),
      percentage: 15,
    },
    {
      toolId: 'product-description',
      toolName: 'Product Description',
      category: 'business',
      count: 142,
      lastUsedAt: new Date().toISOString(),
      percentage: 11.4,
    },
    {
      toolId: 'meta-description',
      toolName: 'Meta Description',
      category: 'seo',
      count: 98,
      lastUsedAt: new Date().toISOString(),
      percentage: 7.9,
    },
    {
      toolId: 'brand-name-generator',
      toolName: 'Brand Name Generator',
      category: 'naming',
      count: 87,
      lastUsedAt: new Date().toISOString(),
      percentage: 7,
    },
    {
      toolId: 'youtube-title',
      toolName: 'YouTube Title',
      category: 'video',
      count: 76,
      lastUsedAt: new Date().toISOString(),
      percentage: 6.1,
    },
    {
      toolId: 'content-rewriter',
      toolName: 'Content Rewriter',
      category: 'rewriting',
      count: 65,
      lastUsedAt: new Date().toISOString(),
      percentage: 5.2,
    },
  ]
}

function getMockTimelineData(timeRange: TimeRangeOption): TimelineDataPoint[] {
  const days = timeRange === '7d' ? 7 : timeRange === '30d' ? 30 : 90
  const data: TimelineDataPoint[] = []
  const now = new Date()

  for (let i = days - 1; i >= 0; i--) {
    const date = new Date(now.getTime() - i * 24 * 60 * 60 * 1000)
    const dateStr = date.toISOString().split('T')[0]
    // Generate realistic-looking data with some variation
    const baseCount = 30 + Math.floor(Math.random() * 20)
    const weekendFactor = date.getDay() === 0 || date.getDay() === 6 ? 0.6 : 1
    const trendFactor = 1 + (days - i) * 0.01 // Slight upward trend

    data.push({
      date: dateStr,
      count: Math.floor(baseCount * weekendFactor * trendFactor),
      label: formatDateLabel(dateStr, timeRange),
    })
  }

  return data
}

function getMockCategoryBreakdown(): CategoryBreakdown[] {
  return [
    { category: 'blog', count: 412, percentage: 33, color: CATEGORY_COLORS.blog },
    { category: 'email', count: 268, percentage: 21.5, color: CATEGORY_COLORS.email },
    {
      category: 'social-media',
      count: 224,
      percentage: 18,
      color: CATEGORY_COLORS['social-media'],
    },
    { category: 'business', count: 156, percentage: 12.5, color: CATEGORY_COLORS.business },
    { category: 'seo', count: 98, percentage: 7.9, color: CATEGORY_COLORS.seo },
    { category: 'naming', count: 45, percentage: 3.6, color: CATEGORY_COLORS.naming },
    { category: 'video', count: 32, percentage: 2.6, color: CATEGORY_COLORS.video },
    { category: 'rewriting', count: 12, percentage: 0.9, color: CATEGORY_COLORS.rewriting },
  ]
}

export const analyticsApi = {
  getOverviewStats,
  getToolUsageStats,
  getTimelineData,
  getCategoryBreakdown,
}

export default analyticsApi
