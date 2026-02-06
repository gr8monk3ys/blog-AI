'use client'

import Link from 'next/link'
import { motion } from 'framer-motion'
import { Template, TEMPLATE_CATEGORIES } from '../../types/templates'
import {
  DocumentTextIcon,
  EnvelopeIcon,
  ChatBubbleLeftRightIcon,
  VideoCameraIcon,
  ShoppingBagIcon,
  RocketLaunchIcon,
  PencilSquareIcon,
  BriefcaseIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline'

interface TemplateCardProps {
  template: Template
  index?: number
  onUse?: (template: Template) => void
}

const categoryIcons: Record<string, React.ElementType> = {
  marketing: RocketLaunchIcon,
  saas: RocketLaunchIcon,
  ecommerce: ShoppingBagIcon,
  content: PencilSquareIcon,
  social: ChatBubbleLeftRightIcon,
  email: EnvelopeIcon,
  video: VideoCameraIcon,
  business: BriefcaseIcon,
  other: DocumentTextIcon,
}

export default function TemplateCard({ template, index = 0, onUse }: TemplateCardProps) {
  const categoryInfo = TEMPLATE_CATEGORIES[template.category] || TEMPLATE_CATEGORIES.other
  const Icon = categoryIcons[template.category] || DocumentTextIcon

  const handleUseClick = (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    onUse?.(template)
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.05 }}
    >
      <div className="relative h-full bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md hover:border-amber-200 transition-all duration-200 overflow-hidden">
        {/* Top badges row */}
        <div className="absolute top-3 right-3 flex items-center gap-2">
          {template.useCount > 100 && (
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-700 border border-amber-200">
              Popular
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
          <h3 className="text-base font-semibold text-gray-900 mb-2 line-clamp-1">
            {template.name}
          </h3>

          {/* Description */}
          <p className="text-sm text-gray-600 line-clamp-2 leading-relaxed mb-3">
            {template.description || 'No description available'}
          </p>

          {/* Tags */}
          {template.tags.length > 0 && (
            <div className="flex flex-wrap gap-1 mb-4">
              {template.tags.slice(0, 3).map((tag) => (
                <span
                  key={tag}
                  className="inline-flex items-center px-2 py-0.5 rounded text-xs text-gray-500 bg-gray-100"
                >
                  {tag}
                </span>
              ))}
              {template.tags.length > 3 && (
                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs text-gray-400">
                  +{template.tags.length - 3}
                </span>
              )}
            </div>
          )}

          {/* Stats */}
          <div className="flex items-center justify-between text-xs text-gray-500 mb-4">
            <span className="flex items-center gap-1">
              <SparklesIcon className="w-3.5 h-3.5" />
              {template.useCount} uses
            </span>
          </div>
        </div>

        {/* Bottom action */}
        <div className="px-5 pb-4">
          <button
            type="button"
            onClick={handleUseClick}
            className="w-full flex justify-center items-center py-2.5 px-4 border border-transparent rounded-lg text-sm font-medium text-white bg-gradient-to-r from-amber-600 to-amber-700 hover:from-amber-700 hover:to-amber-800 shadow-sm transition-all focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2"
          >
            Use Template
          </button>
        </div>
      </div>
    </motion.div>
  )
}
