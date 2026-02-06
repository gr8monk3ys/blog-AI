'use client'

import { motion } from 'framer-motion'
import {
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
} from '@heroicons/react/24/outline'

interface StatCardProps {
  title: string
  value: string | number
  subtitle?: string
  icon: React.ElementType
  change?: number
  changeLabel?: string
  loading?: boolean
}

export default function StatCard({
  title,
  value,
  subtitle,
  icon: Icon,
  change,
  changeLabel,
  loading = false,
}: StatCardProps) {
  const isPositiveChange = change !== undefined && change >= 0

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 hover:shadow-md transition-shadow"
    >
      {loading ? (
        <div className="animate-pulse">
          <div className="flex items-center justify-between mb-4">
            <div className="h-4 bg-gray-200 rounded w-24" />
            <div className="h-10 w-10 bg-gray-200 rounded-lg" />
          </div>
          <div className="h-8 bg-gray-200 rounded w-20 mb-2" />
          <div className="h-4 bg-gray-200 rounded w-32" />
        </div>
      ) : (
        <>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-gray-500">{title}</h3>
            <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center">
              <Icon className="w-5 h-5 text-amber-600" aria-hidden="true" />
            </div>
          </div>

          <div className="flex items-baseline gap-2">
            <p className="text-2xl font-bold text-gray-900">{value}</p>
            {change !== undefined && (
              <span
                className={`inline-flex items-center text-sm font-medium ${
                  isPositiveChange ? 'text-emerald-600' : 'text-red-600'
                }`}
              >
                {isPositiveChange ? (
                  <ArrowTrendingUpIcon className="w-4 h-4 mr-0.5" aria-hidden="true" />
                ) : (
                  <ArrowTrendingDownIcon className="w-4 h-4 mr-0.5" aria-hidden="true" />
                )}
                {Math.abs(change).toFixed(1)}%
              </span>
            )}
          </div>

          {(subtitle || changeLabel) && (
            <p className="mt-1 text-sm text-gray-500">
              {subtitle}
              {changeLabel && (
                <span className="text-gray-400"> {changeLabel}</span>
              )}
            </p>
          )}
        </>
      )}
    </motion.div>
  )
}
