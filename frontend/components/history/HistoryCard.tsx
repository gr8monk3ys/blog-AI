'use client'

import { useState } from 'react'
import Link from 'next/link'
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
  ClockIcon,
  TrashIcon,
  ArrowTopRightOnSquareIcon,
  ClipboardDocumentIcon,
  CheckIcon,
} from '@heroicons/react/24/outline'
import FavoriteButton from './FavoriteButton'
import type { GeneratedContentItem } from '../../types/history'
import { TOOL_CATEGORIES, ToolCategory } from '../../types/tools'

interface HistoryCardProps {
  item: GeneratedContentItem
  index?: number
  onDelete?: (id: string) => void
  onFavoriteToggle?: (id: string, newStatus: boolean) => void
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
 * Map tool_id to category
 */
function getToolCategory(toolId: string): ToolCategory {
  const categoryMap: Record<string, ToolCategory> = {
    'blog-post-generator': 'blog',
    'blog-outline': 'blog',
    'blog-intro-generator': 'blog',
    'blog-conclusion': 'blog',
    'email-subject-lines': 'email',
    'cold-email-generator': 'email',
    'newsletter-writer': 'email',
    'follow-up-email': 'email',
    'instagram-caption': 'social-media',
    'twitter-thread': 'social-media',
    'linkedin-post': 'social-media',
    'facebook-ad-copy': 'social-media',
    'business-plan': 'business',
    'product-description': 'business',
    'press-release': 'business',
    'proposal-writer': 'business',
    'brand-name-generator': 'naming',
    'tagline-generator': 'naming',
    'domain-name-ideas': 'naming',
    'youtube-title': 'video',
    'video-script': 'video',
    'youtube-description': 'video',
    'meta-description': 'seo',
    'keyword-research': 'seo',
    'seo-title': 'seo',
    'content-rewriter': 'rewriting',
    'sentence-rewriter': 'rewriting',
    'tone-changer': 'rewriting',
    'grammar-improver': 'rewriting',
  }
  return categoryMap[toolId] || 'blog'
}

/**
 * Format date to relative time
 */
function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / (1000 * 60))
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`

  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined,
  })
}

/**
 * Truncate text to a maximum length
 */
function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text
  return text.slice(0, maxLength).trim() + '...'
}

/**
 * Get a preview title from the content
 */
function getPreviewTitle(item: GeneratedContentItem): string {
  // Use explicit title if available
  if (item.title) return item.title

  // Try to extract from inputs
  const inputs = item.inputs as Record<string, unknown>
  if (inputs.topic) return String(inputs.topic)
  if (inputs.title) return String(inputs.title)
  if (inputs.subject) return String(inputs.subject)

  // Extract first line of output
  const lines = item.output.split('\n')
  const firstLine = (lines[0] || '').replace(/^#+\s*/, '')
  return truncateText(firstLine || 'Untitled', 60)
}

export default function HistoryCard({
  item,
  index = 0,
  onDelete,
  onFavoriteToggle,
}: HistoryCardProps) {
  const [copied, setCopied] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)

  const category = getToolCategory(item.tool_id)
  const categoryInfo = TOOL_CATEGORIES[category]
  const Icon = categoryIcons[category] || DocumentTextIcon

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(item.output)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  const handleDelete = async () => {
    if (!onDelete || isDeleting) return
    if (!confirm('Are you sure you want to delete this content?')) return

    setIsDeleting(true)
    try {
      await onDelete(item.id)
    } catch (err) {
      console.error('Failed to delete:', err)
      setIsDeleting(false)
    }
  }

  const previewTitle = getPreviewTitle(item)
  const previewOutput = truncateText(
    item.output.replace(/^#+\s*[^\n]+\n*/, '').replace(/\n/g, ' '),
    150
  )

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.3, delay: index * 0.05 }}
      className={`group relative bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md hover:border-indigo-200 transition-all duration-200 overflow-hidden ${
        isDeleting ? 'opacity-50 pointer-events-none' : ''
      }`}
    >
      {/* Favorite indicator stripe */}
      {item.is_favorite && (
        <div
          className="absolute left-0 top-0 bottom-0 w-1 bg-gradient-to-b from-amber-400 to-amber-500"
          aria-hidden="true"
        />
      )}

      <div className="p-5">
        {/* Header */}
        <div className="flex items-start justify-between gap-3 mb-3">
          <div className="flex items-start gap-3 min-w-0 flex-1">
            <div
              className={`flex-shrink-0 w-10 h-10 rounded-lg ${categoryInfo.bgColor} flex items-center justify-center`}
            >
              <Icon className={`w-5 h-5 ${categoryInfo.color}`} aria-hidden="true" />
            </div>
            <div className="min-w-0 flex-1">
              <h3 className="text-base font-semibold text-gray-900 truncate">
                {previewTitle}
              </h3>
              <div className="flex items-center gap-2 mt-1">
                <span
                  className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium ${categoryInfo.bgColor} ${categoryInfo.color} border ${categoryInfo.borderColor}`}
                >
                  {item.tool_name || item.tool_id}
                </span>
                <span className="inline-flex items-center text-xs text-gray-500">
                  <ClockIcon className="w-3.5 h-3.5 mr-1" aria-hidden="true" />
                  {formatRelativeTime(item.created_at)}
                </span>
              </div>
            </div>
          </div>

          {/* Favorite button */}
          <FavoriteButton
            contentId={item.id}
            isFavorite={item.is_favorite}
            onToggle={(newStatus) => onFavoriteToggle?.(item.id, newStatus)}
            size="md"
          />
        </div>

        {/* Preview */}
        <p className="text-sm text-gray-600 line-clamp-3 mb-4">{previewOutput}</p>

        {/* Actions */}
        <div className="flex items-center justify-between pt-3 border-t border-gray-100">
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleCopy}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-700 bg-gray-50 border border-gray-200 rounded-md hover:bg-gray-100 transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-1"
              aria-label="Copy to clipboard"
            >
              {copied ? (
                <>
                  <CheckIcon className="w-3.5 h-3.5 text-emerald-500" aria-hidden="true" />
                  Copied
                </>
              ) : (
                <>
                  <ClipboardDocumentIcon className="w-3.5 h-3.5" aria-hidden="true" />
                  Copy
                </>
              )}
            </button>

            <Link
              href={`/tools/${item.tool_id}?from=${item.id}`}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-indigo-700 bg-indigo-50 border border-indigo-200 rounded-md hover:bg-indigo-100 transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-1"
              aria-label="Reuse this content"
            >
              <ArrowTopRightOnSquareIcon className="w-3.5 h-3.5" aria-hidden="true" />
              Reuse
            </Link>
          </div>

          <button
            type="button"
            onClick={handleDelete}
            disabled={isDeleting}
            className="inline-flex items-center gap-1.5 px-2 py-1.5 text-xs font-medium text-gray-400 hover:text-red-600 transition-colors focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-1 rounded-md opacity-0 group-hover:opacity-100"
            aria-label="Delete this content"
          >
            <TrashIcon className="w-4 h-4" aria-hidden="true" />
          </button>
        </div>
      </div>
    </motion.div>
  )
}
