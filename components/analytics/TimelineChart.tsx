'use client'

import { useMemo } from 'react'
import { motion } from 'framer-motion'
import type { TimelineDataPoint } from '../../types/analytics'

interface TimelineChartProps {
  data: TimelineDataPoint[]
  title?: string
  loading?: boolean
  height?: number
}

export default function TimelineChart({
  data,
  title = 'Generation Activity',
  loading = false,
  height = 200,
}: TimelineChartProps) {
  const chartData = useMemo(() => {
    if (data.length === 0) return { points: [], max: 0, min: 0 }

    const counts = data.map((d) => d.count)
    const max = Math.max(...counts)
    const min = Math.min(...counts)

    // Calculate SVG path and points
    const padding = { top: 20, right: 20, bottom: 40, left: 50 }
    const chartHeight = height - padding.top - padding.bottom

    const xStep = data.length > 1 ? 100 / (data.length - 1) : 0
    const yScale = max > min ? chartHeight / (max - min) : 1

    const points = data.map((d, i) => ({
      x: i * xStep,
      y: padding.top + (max - d.count) * yScale,
      ...d,
    }))

    return { points, max, min, padding, chartHeight }
  }, [data, height])

  const pathD = useMemo(() => {
    if (chartData.points.length === 0) return ''

    const { points } = chartData
    return points
      .map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x}% ${p.y}`)
      .join(' ')
  }, [chartData])

  const areaPathD = useMemo(() => {
    if (chartData.points.length === 0) return ''

    const { points, padding, chartHeight } = chartData
    const bottomY = padding!.top + chartHeight!

    const lastPoint = points[points.length - 1]
    const firstPoint = points[0]
    if (!lastPoint || !firstPoint) return ''

    return (
      points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x}% ${p.y}`).join(' ') +
      ` L ${lastPoint.x}% ${bottomY}` +
      ` L ${firstPoint.x}% ${bottomY} Z`
    )
  }, [chartData])

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>

      {loading ? (
        <div className="animate-pulse" style={{ height }}>
          <div className="h-full bg-gray-100 rounded" />
        </div>
      ) : data.length === 0 ? (
        <div className="flex items-center justify-center" style={{ height }}>
          <p className="text-gray-500">No timeline data available</p>
        </div>
      ) : (
        <div className="relative" style={{ height }}>
          {/* Y-axis labels */}
          <div className="absolute left-0 top-5 bottom-10 w-10 flex flex-col justify-between text-xs text-gray-500">
            <span>{chartData.max}</span>
            <span>{Math.round((chartData.max + chartData.min) / 2)}</span>
            <span>{chartData.min}</span>
          </div>

          {/* Chart area */}
          <div className="absolute left-12 right-0 top-0 bottom-0">
            <svg
              viewBox="0 0 100 100"
              preserveAspectRatio="none"
              className="w-full h-full"
              style={{ height: height - 40 }}
            >
              {/* Grid lines */}
              <line
                x1="0"
                y1="33%"
                x2="100%"
                y2="33%"
                stroke="#e5e7eb"
                strokeWidth="0.5"
                vectorEffect="non-scaling-stroke"
              />
              <line
                x1="0"
                y1="66%"
                x2="100%"
                y2="66%"
                stroke="#e5e7eb"
                strokeWidth="0.5"
                vectorEffect="non-scaling-stroke"
              />

              {/* Area fill */}
              <motion.path
                d={areaPathD}
                fill="url(#areaGradient)"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.5 }}
              />

              {/* Line */}
              <motion.path
                d={pathD}
                fill="none"
                stroke="#4f46e5"
                strokeWidth="2"
                vectorEffect="non-scaling-stroke"
                strokeLinecap="round"
                strokeLinejoin="round"
                initial={{ pathLength: 0 }}
                animate={{ pathLength: 1 }}
                transition={{ duration: 1, ease: 'easeInOut' }}
              />

              {/* Data points */}
              {chartData.points.map((point, i) => (
                <motion.circle
                  key={i}
                  cx={`${point.x}%`}
                  cy={point.y}
                  r="3"
                  fill="#4f46e5"
                  className="hover:r-4 transition-all cursor-pointer"
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: 0.5 + i * 0.02 }}
                >
                  <title>
                    {point.label}: {point.count} generations
                  </title>
                </motion.circle>
              ))}

              {/* Gradient definition */}
              <defs>
                <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#4f46e5" stopOpacity="0.3" />
                  <stop offset="100%" stopColor="#4f46e5" stopOpacity="0.05" />
                </linearGradient>
              </defs>
            </svg>

            {/* X-axis labels */}
            <div className="flex justify-between text-xs text-gray-500 mt-2">
              {data.length <= 7 ? (
                data.map((d, i) => (
                  <span key={i} className="text-center">
                    {d.label}
                  </span>
                ))
              ) : (
                <>
                  <span>{data[0]?.label}</span>
                  <span>{data[Math.floor(data.length / 2)]?.label}</span>
                  <span>{data[data.length - 1]?.label}</span>
                </>
              )}
            </div>
          </div>

          {/* Hover tooltip area */}
          <div className="absolute inset-0 flex">
            {chartData.points.map((point, i) => (
              <div
                key={i}
                className="flex-1 group relative"
                style={{ cursor: 'crosshair' }}
              >
                <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10">
                  <div className="bg-gray-900 text-white text-xs rounded px-2 py-1 whitespace-nowrap">
                    <div className="font-medium">{point.label}</div>
                    <div>{point.count} generations</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
