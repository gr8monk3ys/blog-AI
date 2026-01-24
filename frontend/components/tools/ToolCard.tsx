'use client'

import Link from 'next/link'
import { motion } from 'framer-motion'
import { Tool, TOOL_CATEGORIES } from '../../types/tools'
import {
  DocumentTextIcon,
  EnvelopeIcon,
  ChatBubbleLeftRightIcon,
  BriefcaseIcon,
  SparklesIcon,
  VideoCameraIcon,
  MagnifyingGlassIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline'

interface ToolCardProps {
  tool: Tool
  index?: number
}

const categoryIcons: Record<string, React.ElementType> = {
  blog: DocumentTextIcon,
  email: EnvelopeIcon,
  'social-media': ChatBubbleLeftRightIcon,
  business: BriefcaseIcon,
  naming: SparklesIcon,
  video: VideoCameraIcon,
  seo: MagnifyingGlassIcon,
  rewriting: ArrowPathIcon,
}

export default function ToolCard({ tool, index = 0 }: ToolCardProps) {
  const categoryInfo = TOOL_CATEGORIES[tool.category]
  const Icon = categoryIcons[tool.category] || DocumentTextIcon

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.05 }}
    >
      <Link
        href={`/tools/${tool.slug}`}
        className="block group"
        aria-label={`Open ${tool.name} tool`}
      >
        <div className="relative h-full bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md hover:border-indigo-200 transition-all duration-200 overflow-hidden">
          {/* Top badges row */}
          <div className="absolute top-3 right-3 flex items-center gap-2">
            {tool.isNew && (
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gradient-to-r from-indigo-500 to-purple-500 text-white">
                New
              </span>
            )}
            {tool.isPopular && (
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-700 border border-amber-200">
                Popular
              </span>
            )}
            {tool.isFree && (
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-700 border border-emerald-200">
                Free
              </span>
            )}
          </div>

          <div className="p-5">
            {/* Icon and Category */}
            <div className="flex items-start gap-4 mb-3">
              <div
                className={`flex-shrink-0 w-10 h-10 rounded-lg ${categoryInfo.bgColor} flex items-center justify-center`}
              >
                <Icon className={`w-5 h-5 ${categoryInfo.color}`} aria-hidden="true" />
              </div>
              <div className="flex-1 min-w-0 pt-1">
                <span
                  className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium ${categoryInfo.bgColor} ${categoryInfo.color} border ${categoryInfo.borderColor}`}
                >
                  {categoryInfo.name}
                </span>
              </div>
            </div>

            {/* Title */}
            <h3 className="text-base font-semibold text-gray-900 group-hover:text-indigo-600 transition-colors mb-2 line-clamp-1">
              {tool.name}
            </h3>

            {/* Description */}
            <p className="text-sm text-gray-600 line-clamp-2 leading-relaxed">
              {tool.description}
            </p>
          </div>

          {/* Bottom action indicator */}
          <div className="px-5 pb-4">
            <div className="flex items-center text-sm font-medium text-indigo-600 group-hover:text-indigo-700 transition-colors">
              <span>Try it now</span>
              <svg
                className="w-4 h-4 ml-1 group-hover:translate-x-1 transition-transform"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5l7 7-7 7"
                />
              </svg>
            </div>
          </div>
        </div>
      </Link>
    </motion.div>
  )
}
