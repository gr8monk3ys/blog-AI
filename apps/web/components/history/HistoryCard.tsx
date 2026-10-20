'use client'

import { useState } from 'react'
import Link from 'next/link'
import {
  TrashIcon,
  ArrowTopRightOnSquareIcon,
  ClipboardDocumentIcon,
  CheckIcon,
} from '@heroicons/react/24/outline'
import FavoriteButton from './FavoriteButton'
import { Button, buttonVariants } from '../ui/Button'
import { useConfirmModal } from '../../hooks/useConfirmModal'
import { cn } from '../../lib/cn'
import type { GeneratedContentItem } from '../../types/history'
import { TOOL_CATEGORIES, ToolCategory } from '../../types/tools'

interface HistoryCardProps {
  item: GeneratedContentItem
  onDelete?: (id: string) => void
  onFavoriteToggle?: (id: string, newStatus: boolean) => void
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

/**
 * One history entry as a row in a hairline-divided list (DESIGN.md →
 * Components → Cards / Rows): the catalogue line in mono above — category,
 * tool, when — a semibold title, a two-line clamped preview in Ink Muted,
 * and the actions beneath. The category used to be a coloured tile; it is
 * now a word in the wall label.
 */
export default function HistoryCard({ item, onDelete, onFavoriteToggle }: HistoryCardProps) {
  const { confirm, ConfirmModalComponent } = useConfirmModal()
  const [copied, setCopied] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)

  const category = getToolCategory(item.tool_id)
  const categoryInfo = TOOL_CATEGORIES[category]

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

    const confirmed = await confirm({
      title: 'Delete Content',
      message: 'Are you sure you want to delete this content? This action cannot be undone.',
      confirmLabel: 'Delete',
      cancelLabel: 'Cancel',
      variant: 'danger',
    })

    if (!confirmed) return

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
    <li className={cn('py-4 sm:py-5', isDeleting && 'pointer-events-none opacity-50')}>
      <ConfirmModalComponent />

      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <p className="label-mono">
            {categoryInfo.name} · {item.tool_name || item.tool_id} ·{' '}
            <time dateTime={item.created_at}>{formatRelativeTime(item.created_at)}</time>
            {item.is_favorite ? ' · favourite' : null}
          </p>
          <h3 className="mt-1.5 truncate text-base font-semibold text-foreground">{previewTitle}</h3>
          <p className="mt-1 line-clamp-2 text-sm text-muted-foreground">{previewOutput}</p>
        </div>

        <FavoriteButton
          contentId={item.id}
          isFavorite={item.is_favorite}
          onToggle={(newStatus) => onFavoriteToggle?.(item.id, newStatus)}
          size="md"
        />
      </div>

      <div className="mt-3 flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <Button type="button" variant="ghost" size="sm" onClick={handleCopy} aria-label="Copy to clipboard">
            {copied ? (
              <>
                <CheckIcon className="h-4 w-4 text-success" aria-hidden="true" />
                Copied
              </>
            ) : (
              <>
                <ClipboardDocumentIcon className="h-4 w-4" aria-hidden="true" />
                Copy
              </>
            )}
          </Button>

          <Link
            href={`/tools/${item.tool_id}?from=${item.id}`}
            className={buttonVariants({ variant: 'secondary', size: 'sm' })}
            aria-label="Reuse this content"
          >
            <ArrowTopRightOnSquareIcon className="h-4 w-4" aria-hidden="true" />
            Reuse
          </Link>
        </div>

        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={handleDelete}
          disabled={isDeleting}
          className="text-muted-foreground hover:text-destructive"
          aria-label="Delete this content"
        >
          <TrashIcon className="h-4 w-4" aria-hidden="true" />
        </Button>
      </div>
    </li>
  )
}
