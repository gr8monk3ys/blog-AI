'use client'

import { motion } from 'framer-motion'
import Link from 'next/link'
import {
  ClipboardDocumentIcon,
  CheckIcon,
  ClockIcon,
  BookmarkIcon,
} from '@heroicons/react/24/outline'
import ExportMenu from '../../ExportMenu'
import FavoriteButton from '../../history/FavoriteButton'
import ContentScore from '../ContentScore'
import VariationCompare from '../VariationCompare'
import type { ExportContent, ExportFormat } from '../../ExportMenu'
import type { ContentScoreResult } from '../ContentScore'
import type { ContentVariation } from '../VariationCompare'
import type { Tool } from '../../../types/tools'

interface ToolOutputProps {
  tool: Tool
  inputText: string
  output: string | null
  variations: ContentVariation[]
  selectedVariation: ContentVariation | null
  onVariationSelect: (variation: ContentVariation) => void
  contentScore: ContentScoreResult | null
  scoringLoading: boolean
  savedContentId: string | null
  isFavorite: boolean
  onFavoriteToggle: (newStatus: boolean) => void
  copied: boolean
  onCopy: () => void
  onExportComplete: (format: ExportFormat, success: boolean) => void
  onSaveTemplateClick: () => void
  loading: boolean
}

/**
 * Get export content from tool output
 */
function getExportContent(
  tool: Tool,
  inputText: string,
  output: string
): ExportContent {
  return {
    title: `${tool.name} - ${inputText.substring(0, 50)}${inputText.length > 50 ? '...' : ''}`,
    content: output,
    type: 'tool',
    metadata: {
      date: new Date().toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      }),
      toolName: tool.name,
      description: tool.description,
    },
  }
}

/**
 * Output section displaying generated content and variations
 */
export default function ToolOutput({
  tool,
  inputText,
  output,
  variations,
  selectedVariation,
  onVariationSelect,
  contentScore,
  scoringLoading,
  savedContentId,
  isFavorite,
  onFavoriteToggle,
  copied,
  onCopy,
  onExportComplete,
  onSaveTemplateClick,
  loading,
}: ToolOutputProps) {
  return (
    <>
      {/* Variations comparison section */}
      {variations.length > 0 && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          className="border-t border-gray-200 bg-gray-50"
        >
          <div className="p-6">
            <VariationCompare
              variations={variations}
              isLoading={loading}
              onSelect={onVariationSelect}
              selectedId={selectedVariation?.id}
            />
          </div>
        </motion.div>
      )}

      {/* Output section */}
      {output && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          className="border-t border-gray-200 bg-gray-50"
        >
          <div className="p-6">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-3">
                <h3 className="text-sm font-medium text-gray-900">
                  {selectedVariation
                    ? `Selected Content (Version ${selectedVariation.label})`
                    : 'Generated Content'}
                </h3>
                {savedContentId && (
                  <FavoriteButton
                    contentId={savedContentId}
                    isFavorite={isFavorite}
                    onToggle={onFavoriteToggle}
                    size="sm"
                  />
                )}
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={onCopy}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
                >
                  {copied ? (
                    <>
                      <CheckIcon className="w-3.5 h-3.5 text-emerald-500" />
                      Copied!
                    </>
                  ) : (
                    <>
                      <ClipboardDocumentIcon className="w-3.5 h-3.5" />
                      Copy
                    </>
                  )}
                </button>
                <ExportMenu
                  content={getExportContent(tool, inputText, output)}
                  onExportComplete={onExportComplete}
                />
              </div>
            </div>
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <p className="text-sm text-gray-700 whitespace-pre-wrap">
                {output}
              </p>
            </div>

            {/* Content Score display */}
            {(contentScore || scoringLoading) && (
              <div className="mt-4">
                <ContentScore
                  scores={contentScore!}
                  isLoading={scoringLoading}
                  showDetails={true}
                />
              </div>
            )}

            {/* Save as Template and History indicator */}
            <div className="mt-4 flex items-center justify-between">
              <button
                type="button"
                onClick={onSaveTemplateClick}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-amber-700 bg-amber-50 border border-amber-200 rounded-md hover:bg-amber-100 transition-colors"
              >
                <BookmarkIcon className="w-3.5 h-3.5" />
                Save as Template
              </button>

              {savedContentId && (
                <div className="flex items-center gap-2 text-xs text-gray-500">
                  <span className="inline-flex items-center gap-1">
                    <ClockIcon className="w-3.5 h-3.5" aria-hidden="true" />
                    Saved to history
                  </span>
                  <Link
                    href="/history"
                    className="inline-flex items-center gap-1 text-amber-600 hover:text-amber-700 transition-colors"
                  >
                    View history
                    <svg
                      className="w-3 h-3"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 5l7 7-7 7"
                      />
                    </svg>
                  </Link>
                </div>
              )}
            </div>
          </div>
        </motion.div>
      )}
    </>
  )
}
