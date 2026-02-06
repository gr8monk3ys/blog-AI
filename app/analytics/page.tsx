'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { motion } from 'framer-motion'
import {
  ArrowLeftIcon,
  SparklesIcon,
  ChartBarIcon,
  ClockIcon,
  FireIcon,
  BoltIcon,
} from '@heroicons/react/24/outline'

import { StatCard, BarChart, TimelineChart, PieChart } from '../../components/analytics'
import {
  getOverviewStats,
  getToolUsageStats,
  getTimelineData,
  getCategoryBreakdown,
} from '../../lib/analytics-api'
import type {
  OverviewStats,
  ToolUsageStat,
  TimelineDataPoint,
  CategoryBreakdown,
  TimeRangeOption,
} from '../../types/analytics'
import { TIME_RANGE_OPTIONS } from '../../types/analytics'

export default function AnalyticsPage() {
  const [timeRange, setTimeRange] = useState<TimeRangeOption>('30d')
  const [loading, setLoading] = useState(true)
  const [overviewStats, setOverviewStats] = useState<OverviewStats | null>(null)
  const [toolUsage, setToolUsage] = useState<ToolUsageStat[]>([])
  const [timelineData, setTimelineData] = useState<TimelineDataPoint[]>([])
  const [categoryData, setCategoryData] = useState<CategoryBreakdown[]>([])

  useEffect(() => {
    async function fetchData() {
      setLoading(true)
      try {
        const [overview, tools, timeline, categories] = await Promise.all([
          getOverviewStats(timeRange),
          getToolUsageStats(timeRange),
          getTimelineData(timeRange),
          getCategoryBreakdown(timeRange),
        ])

        setOverviewStats(overview)
        setToolUsage(tools)
        setTimelineData(timeline)
        setCategoryData(categories)
      } catch (error) {
        console.error('Failed to fetch analytics data:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [timeRange])

  const formatExecutionTime = (ms: number): string => {
    if (ms < 1000) return `${ms}ms`
    return `${(ms / 1000).toFixed(1)}s`
  }

  const formatToolName = (toolId: string | null): string => {
    if (!toolId) return 'N/A'
    return toolId
      .split('-')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ')
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <Link
                href="/"
                className="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 transition-colors"
              >
                <ArrowLeftIcon className="w-4 h-4" aria-hidden="true" />
                <span>Back to Generator</span>
              </Link>
            </div>
            <div className="flex items-center gap-2">
              <SparklesIcon className="w-5 h-5 text-indigo-600" aria-hidden="true" />
              <span className="font-semibold text-gray-900">Blog AI</span>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="bg-gradient-to-r from-indigo-600 to-indigo-700 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 sm:py-12">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div>
                <h1 className="text-2xl sm:text-3xl font-bold mb-2">
                  Analytics Dashboard
                </h1>
                <p className="text-indigo-100">
                  Track your content generation activity and tool usage
                </p>
              </div>

              {/* Time Range Selector */}
              <div className="flex items-center gap-2 bg-white/10 rounded-lg p-1">
                {(Object.keys(TIME_RANGE_OPTIONS) as TimeRangeOption[]).map(
                  (range) => (
                    <button
                      key={range}
                      onClick={() => setTimeRange(range)}
                      className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all ${
                        timeRange === range
                          ? 'bg-white text-indigo-600'
                          : 'text-white/80 hover:text-white hover:bg-white/10'
                      }`}
                    >
                      {TIME_RANGE_OPTIONS[range].label}
                    </button>
                  )
                )}
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Main Content */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Overview Stats */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8"
        >
          <StatCard
            title="Total Generations"
            value={overviewStats?.totalGenerations.toLocaleString() || '0'}
            icon={ChartBarIcon}
            change={overviewStats?.generationsChange}
            changeLabel="vs previous period"
            loading={loading}
          />
          <StatCard
            title="Active Today"
            value={overviewStats?.activeToday.toLocaleString() || '0'}
            icon={FireIcon}
            subtitle="Generations today"
            loading={loading}
          />
          <StatCard
            title="Popular Tool"
            value={formatToolName(overviewStats?.popularTool || null)}
            icon={SparklesIcon}
            subtitle="Most used tool"
            loading={loading}
          />
          <StatCard
            title="Avg. Response Time"
            value={formatExecutionTime(overviewStats?.averageExecutionTime || 0)}
            icon={BoltIcon}
            subtitle="Per generation"
            loading={loading}
          />
        </motion.div>

        {/* Charts Row 1 */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6"
        >
          <TimelineChart
            data={timelineData}
            title="Generation Activity"
            loading={loading}
            height={250}
          />
          <BarChart
            data={toolUsage}
            title="Most Used Tools"
            loading={loading}
            maxBars={6}
          />
        </motion.div>

        {/* Charts Row 2 */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="grid grid-cols-1 lg:grid-cols-3 gap-6"
        >
          <div className="lg:col-span-2">
            <BarChart
              data={toolUsage}
              title="Tool Usage Details"
              loading={loading}
              maxBars={10}
            />
          </div>
          <PieChart
            data={categoryData}
            title="Category Distribution"
            loading={loading}
            size={220}
          />
        </motion.div>

        {/* Quick Actions */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.4 }}
          className="mt-8 bg-white rounded-xl border border-gray-200 shadow-sm p-6"
        >
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Quick Actions
          </h3>
          <div className="flex flex-wrap gap-3">
            <Link
              href="/"
              className="inline-flex items-center px-4 py-2 rounded-lg text-sm font-medium text-white bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-700 hover:to-indigo-800 shadow-sm transition-all"
            >
              Generate Content
            </Link>
            <Link
              href="/tools"
              className="inline-flex items-center px-4 py-2 rounded-lg text-sm font-medium text-gray-700 bg-white border border-gray-300 hover:bg-gray-50 shadow-sm transition-all"
            >
              Browse Tools
            </Link>
            <button
              onClick={() => {
                setTimeRange('7d')
              }}
              className="inline-flex items-center px-4 py-2 rounded-lg text-sm font-medium text-gray-700 bg-white border border-gray-300 hover:bg-gray-50 shadow-sm transition-all"
            >
              <ClockIcon className="w-4 h-4 mr-2" aria-hidden="true" />
              View Last 7 Days
            </button>
          </div>
        </motion.div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-50 border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-sm text-gray-500">
            Powered by AI &middot; Blog AI Analytics Dashboard
          </p>
        </div>
      </footer>
    </main>
  )
}
