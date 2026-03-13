/**
 * Analytics API client for Blog-AI
 *
 * Provides methods for fetching analytics data from the backend.
 * Falls back to mock data when backend is unavailable.
 */

import { API_BASE_URL, API_VERSION, apiFetch } from './api'
import type {
  OverviewStats,
  ToolUsageStat,
  TimelineDataPoint,
  CategoryBreakdown,
  TimeRangeOption,
} from '../types/analytics'
import { getCategoryColor } from '../types/analytics'

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
  } catch (err) {
    if (process.env.NODE_ENV === 'production') throw err
    return getMockOverviewStats()
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
  } catch (err) {
    if (process.env.NODE_ENV === 'production') throw err
    return getMockToolUsageStats().slice(0, limit)
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
  } catch (err) {
    if (process.env.NODE_ENV === 'production') throw err
    return getMockTimelineData(timeRange)
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
      color: getCategoryColor(item.category),
    }))
  } catch (err) {
    if (process.env.NODE_ENV === 'production') throw err
    return getMockCategoryBreakdown()
  }
}

// =============================================================================
// Helper Functions
// =============================================================================

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
    const isoString = date.toISOString()
    const dateStr = isoString.split('T')[0] ?? isoString.slice(0, 10)
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
    { category: 'blog', count: 412, percentage: 33, color: getCategoryColor('blog') },
    { category: 'email', count: 268, percentage: 21.5, color: getCategoryColor('email') },
    {
      category: 'social-media',
      count: 224,
      percentage: 18,
      color: getCategoryColor('social-media'),
    },
    { category: 'business', count: 156, percentage: 12.5, color: getCategoryColor('business') },
    { category: 'seo', count: 98, percentage: 7.9, color: getCategoryColor('seo') },
    { category: 'naming', count: 45, percentage: 3.6, color: getCategoryColor('naming') },
    { category: 'video', count: 32, percentage: 2.6, color: getCategoryColor('video') },
    { category: 'rewriting', count: 12, percentage: 0.9, color: getCategoryColor('rewriting') },
  ]
}

export const analyticsApi = {
  getOverviewStats,
  getToolUsageStats,
  getTimelineData,
  getCategoryBreakdown,
}

export default analyticsApi
