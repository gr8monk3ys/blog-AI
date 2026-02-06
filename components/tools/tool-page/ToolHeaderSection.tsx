'use client'

import { motion } from 'framer-motion'
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
import type { Tool, ToolCategoryInfo } from '../../../types/tools'

interface ToolHeaderSectionProps {
  tool: Tool
  categoryInfo: ToolCategoryInfo
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

/**
 * Header section displaying tool name, description, and category badge
 */
export default function ToolHeaderSection({
  tool,
  categoryInfo,
}: ToolHeaderSectionProps) {
  const Icon = categoryIcons[tool.category] || DocumentTextIcon

  return (
    <section className="bg-white border-b border-gray-200">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
        >
          <div className="flex items-start gap-4">
            <div
              className={`flex-shrink-0 w-14 h-14 rounded-xl ${categoryInfo.bgColor} flex items-center justify-center`}
            >
              <Icon
                className={`w-7 h-7 ${categoryInfo.color}`}
                aria-hidden="true"
              />
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-3 flex-wrap">
                <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">
                  {tool.name}
                </h1>
                {tool.isFree && (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-700 border border-emerald-200">
                    Free
                  </span>
                )}
                {tool.isNew && (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gradient-to-r from-amber-500 to-amber-500 text-white">
                    New
                  </span>
                )}
              </div>
              <p className="mt-2 text-gray-600">{tool.description}</p>
              <div className="mt-3">
                <span
                  className={`inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium ${categoryInfo.bgColor} ${categoryInfo.color} border ${categoryInfo.borderColor}`}
                >
                  {categoryInfo.name}
                </span>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  )
}
