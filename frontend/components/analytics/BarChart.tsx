'use client'

import { motion } from 'framer-motion'
import type { ToolUsageStat } from '../../types/analytics'
import { getCategoryColor, getCategoryBgColor } from '../../types/analytics'

interface BarChartProps {
  data: ToolUsageStat[]
  title?: string
  loading?: boolean
  maxBars?: number
}

export default function BarChart({
  data,
  title = 'Tool Usage',
  loading = false,
  maxBars = 8,
}: BarChartProps) {
  const displayData = data.slice(0, maxBars)
  const maxCount = Math.max(...displayData.map((d) => d.count), 1)

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-6">{title}</h3>

      {loading ? (
        <div className="space-y-4">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="animate-pulse">
              <div className="flex items-center justify-between mb-2">
                <div className="h-4 bg-gray-200 rounded w-32" />
                <div className="h-4 bg-gray-200 rounded w-12" />
              </div>
              <div className="h-6 bg-gray-200 rounded" />
            </div>
          ))}
        </div>
      ) : displayData.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-500">No usage data available yet</p>
        </div>
      ) : (
        <div className="space-y-4">
          {displayData.map((item, index) => {
            const barWidth = (item.count / maxCount) * 100
            const barColor = getCategoryColor(item.category)
            const bgColor = getCategoryBgColor(item.category)

            return (
              <motion.div
                key={item.toolId}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 }}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-gray-900">
                      {item.toolName}
                    </span>
                    <span
                      className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium"
                      style={{ backgroundColor: bgColor, color: barColor }}
                    >
                      {formatCategoryLabel(item.category)}
                    </span>
                  </div>
                  <span className="text-sm font-semibold text-gray-700">
                    {item.count.toLocaleString()}
                  </span>
                </div>
                <div className="relative h-6 bg-gray-100 rounded-lg overflow-hidden">
                  <motion.div
                    className="absolute inset-y-0 left-0 rounded-lg"
                    style={{ backgroundColor: barColor }}
                    initial={{ width: 0 }}
                    animate={{ width: `${barWidth}%` }}
                    transition={{ duration: 0.5, delay: index * 0.05 }}
                  />
                  <span className="absolute inset-y-0 right-2 flex items-center text-xs font-medium text-gray-500">
                    {item.percentage.toFixed(1)}%
                  </span>
                </div>
              </motion.div>
            )
          })}
        </div>
      )}
    </div>
  )
}

function formatCategoryLabel(category: string): string {
  return category
    .split('-')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}
