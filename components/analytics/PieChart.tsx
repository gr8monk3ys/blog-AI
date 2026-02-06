'use client'

import { useMemo } from 'react'
import { motion } from 'framer-motion'
import type { CategoryBreakdown } from '../../types/analytics'

interface PieChartProps {
  data: CategoryBreakdown[]
  title?: string
  loading?: boolean
  size?: number
}

interface PieSlice {
  category: string
  count: number
  percentage: number
  color: string
  startAngle: number
  endAngle: number
  path: string
  midAngle: number
  labelX: number
  labelY: number
}

export default function PieChart({
  data,
  title = 'Category Distribution',
  loading = false,
  size = 200,
}: PieChartProps) {
  const slices = useMemo((): PieSlice[] => {
    if (data.length === 0) return []

    const total = data.reduce((sum, d) => sum + d.count, 0)
    if (total === 0) return []

    const cx = size / 2
    const cy = size / 2
    const radius = (size - 20) / 2
    const labelRadius = radius * 0.7

    let currentAngle = -90 // Start from top

    return data.map((d) => {
      const sliceAngle = (d.count / total) * 360
      const startAngle = currentAngle
      const endAngle = currentAngle + sliceAngle
      const midAngle = startAngle + sliceAngle / 2

      // Calculate path
      const startRad = (startAngle * Math.PI) / 180
      const endRad = (endAngle * Math.PI) / 180

      const x1 = cx + radius * Math.cos(startRad)
      const y1 = cy + radius * Math.sin(startRad)
      const x2 = cx + radius * Math.cos(endRad)
      const y2 = cy + radius * Math.sin(endRad)

      const largeArcFlag = sliceAngle > 180 ? 1 : 0

      const path =
        sliceAngle >= 360
          ? `M ${cx} ${cy - radius} A ${radius} ${radius} 0 1 1 ${cx - 0.001} ${cy - radius} Z`
          : `M ${cx} ${cy} L ${x1} ${y1} A ${radius} ${radius} 0 ${largeArcFlag} 1 ${x2} ${y2} Z`

      // Label position
      const labelRad = (midAngle * Math.PI) / 180
      const labelX = cx + labelRadius * Math.cos(labelRad)
      const labelY = cy + labelRadius * Math.sin(labelRad)

      currentAngle = endAngle

      return {
        category: d.category,
        count: d.count,
        percentage: d.percentage,
        color: d.color,
        startAngle,
        endAngle,
        path,
        midAngle,
        labelX,
        labelY,
      }
    })
  }, [data, size])

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>

      {loading ? (
        <div className="flex items-center justify-center" style={{ height: size + 100 }}>
          <div
            className="animate-pulse rounded-full bg-gray-200"
            style={{ width: size, height: size }}
          />
        </div>
      ) : data.length === 0 ? (
        <div
          className="flex items-center justify-center"
          style={{ height: size + 100 }}
        >
          <p className="text-gray-500">No category data available</p>
        </div>
      ) : (
        <div className="flex flex-col items-center">
          {/* Pie Chart SVG */}
          <div className="relative" style={{ width: size, height: size }}>
            <svg viewBox={`0 0 ${size} ${size}`} className="w-full h-full">
              {slices.map((slice, i) => (
                <motion.path
                  key={slice.category}
                  d={slice.path}
                  fill={slice.color}
                  className="cursor-pointer hover:opacity-80 transition-opacity"
                  initial={{ scale: 0, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ delay: i * 0.1, duration: 0.3 }}
                  style={{ transformOrigin: `${size / 2}px ${size / 2}px` }}
                >
                  <title>
                    {formatCategoryLabel(slice.category)}: {slice.count} (
                    {slice.percentage.toFixed(1)}%)
                  </title>
                </motion.path>
              ))}

              {/* Center circle for donut effect */}
              <circle
                cx={size / 2}
                cy={size / 2}
                r={size / 4}
                fill="white"
                className="pointer-events-none"
              />

              {/* Center text */}
              <text
                x={size / 2}
                y={size / 2 - 8}
                textAnchor="middle"
                className="fill-gray-900 font-bold"
                fontSize="18"
              >
                {data.reduce((sum, d) => sum + d.count, 0).toLocaleString()}
              </text>
              <text
                x={size / 2}
                y={size / 2 + 12}
                textAnchor="middle"
                className="fill-gray-500"
                fontSize="12"
              >
                Total
              </text>
            </svg>
          </div>

          {/* Legend */}
          <div className="mt-6 w-full">
            <div className="grid grid-cols-2 gap-3">
              {data.slice(0, 8).map((item, i) => (
                <motion.div
                  key={item.category}
                  className="flex items-center gap-2"
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.3 + i * 0.05 }}
                >
                  <div
                    className="w-3 h-3 rounded-full flex-shrink-0"
                    style={{ backgroundColor: item.color }}
                  />
                  <span className="text-sm text-gray-600 truncate">
                    {formatCategoryLabel(item.category)}
                  </span>
                  <span className="text-sm font-medium text-gray-900 ml-auto">
                    {item.percentage.toFixed(0)}%
                  </span>
                </motion.div>
              ))}
            </div>
          </div>
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
