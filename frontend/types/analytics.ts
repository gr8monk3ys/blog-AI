/**
 * Analytics Types for Blog-AI Dashboard
 */

export interface OverviewStats {
  totalGenerations: number
  totalToolsUsed: number
  activeToday: number
  averageExecutionTime: number
  popularTool: string | null
  generationsChange: number // Percentage change from previous period
}

export interface ToolUsageStat {
  toolId: string
  toolName: string
  category: string
  count: number
  lastUsedAt: string
  percentage: number // Percentage of total usage
}

export interface TimelineDataPoint {
  date: string
  count: number
  label?: string
}

export interface CategoryBreakdown {
  category: string
  count: number
  percentage: number
  color: string
}

export interface AnalyticsTimeRange {
  start: string
  end: string
  label: string
}

export type TimeRangeOption = '7d' | '30d' | '90d' | 'all'

export const TIME_RANGE_OPTIONS: Record<TimeRangeOption, AnalyticsTimeRange> = {
  '7d': {
    start: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
    end: new Date().toISOString(),
    label: 'Last 7 days',
  },
  '30d': {
    start: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
    end: new Date().toISOString(),
    label: 'Last 30 days',
  },
  '90d': {
    start: new Date(Date.now() - 90 * 24 * 60 * 60 * 1000).toISOString(),
    end: new Date().toISOString(),
    label: 'Last 90 days',
  },
  all: {
    start: new Date(0).toISOString(),
    end: new Date().toISOString(),
    label: 'All time',
  },
}

// Category colors matching the design system
export const CATEGORY_COLORS: Record<string, string> = {
  blog: '#4f46e5', // indigo-600
  email: '#059669', // emerald-600
  'social-media': '#db2777', // pink-600
  business: '#475569', // slate-600
  naming: '#d97706', // amber-600
  video: '#dc2626', // red-600
  seo: '#0891b2', // cyan-600
  rewriting: '#7c3aed', // violet-600
}

export const CATEGORY_BG_COLORS: Record<string, string> = {
  blog: '#e0e7ff', // indigo-100
  email: '#d1fae5', // emerald-100
  'social-media': '#fce7f3', // pink-100
  business: '#f1f5f9', // slate-100
  naming: '#fef3c7', // amber-100
  video: '#fee2e2', // red-100
  seo: '#cffafe', // cyan-100
  rewriting: '#ede9fe', // violet-100
}
