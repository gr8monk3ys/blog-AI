'use client'

import React, { useCallback } from 'react'
import { motion } from 'framer-motion'
import type { RemixedContent, ContentFormatInfo } from '@/types/remix'
import { QualityBadge } from './QualityBadge'
import { ContentRenderer } from './ContentRenderer'

// Format icons mapping
const FORMAT_ICONS: Record<string, string> = {
  twitter_thread: '(bird)',
  linkedin_post: '(briefcase)',
  email_newsletter: '(email)',
  youtube_script: '(video)',
  instagram_carousel: '(camera)',
  podcast_notes: '(mic)',
  facebook_post: '(book)',
  tiktok_script: '(music)',
  medium_article: '(pen)',
  press_release: '(news)',
  executive_summary: '(clipboard)',
  slide_deck_outline: '(chart)',
}

interface ResultsPanelProps {
  results: RemixedContent[]
  formats: ContentFormatInfo[]
  selectedResult: RemixedContent | null
  onSelectResult: (result: RemixedContent) => void
}

function ResultsPanelComponent({
  results,
  formats,
  selectedResult,
  onSelectResult,
}: ResultsPanelProps) {
  const handleCopyJson = useCallback(() => {
    if (selectedResult) {
      navigator.clipboard.writeText(
        JSON.stringify(selectedResult.content, null, 2)
      )
    }
  }, [selectedResult])

  const handleCopyText = useCallback(() => {
    if (selectedResult) {
      const content = selectedResult.content as Record<string, unknown>
      const text = Object.values(content)
        .filter((v) => typeof v === 'string')
        .join('\n\n')
      navigator.clipboard.writeText(text)
    }
  }, [selectedResult])

  if (results.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-sm p-12 text-center">
        <div className="text-6xl mb-4">(refresh)</div>
        <h3 className="text-lg font-medium text-gray-900">
          No remixed content yet
        </h3>
        <p className="mt-2 text-gray-500">
          Enter your content, select formats, and click Remix to transform it
        </p>
      </div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      className="bg-white rounded-xl shadow-sm overflow-hidden"
    >
      {/* Format Tabs */}
      <div className="flex overflow-x-auto border-b">
        {results.map((result) => {
          const isActive = selectedResult?.format === result.format
          const formatInfo = formats.find((f) => f.format === result.format)

          return (
            <button
              key={result.format}
              onClick={() => onSelectResult(result)}
              className={`flex-shrink-0 px-4 py-3 flex items-center gap-2 border-b-2 transition-colors ${
                isActive
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-transparent hover:bg-gray-50'
              }`}
            >
              <span>{FORMAT_ICONS[result.format] || '(doc)'}</span>
              <span className="text-sm font-medium">
                {formatInfo?.name || result.format}
              </span>
              <QualityBadge score={result.quality_score} />
            </button>
          )
        })}
      </div>

      {/* Content Preview */}
      {selectedResult && (
        <div className="p-6">
          {/* Metrics */}
          <div className="flex flex-wrap gap-4 mb-6 text-sm text-gray-500">
            <span>{selectedResult.word_count} words</span>
            <span>{selectedResult.character_count} characters</span>
            <span>{selectedResult.generation_time_ms}ms</span>
            {selectedResult.provider_used && (
              <span className="capitalize">{selectedResult.provider_used}</span>
            )}
          </div>

          {/* Quality Breakdown */}
          <div className="mb-6 p-4 bg-gray-50 rounded-lg">
            <h4 className="text-sm font-medium mb-3">Quality Breakdown</h4>
            <div className="grid grid-cols-3 gap-2">
              {Object.entries(selectedResult.quality_score)
                .filter(([key]) => key !== 'overall')
                .map(([key, value]) => (
                  <div key={key} className="text-center">
                    <div className="text-lg font-bold text-blue-600">
                      {Math.round((value as number) * 100)}%
                    </div>
                    <div className="text-xs text-gray-500 capitalize">
                      {key.replace('_', ' ')}
                    </div>
                  </div>
                ))}
            </div>
          </div>

          {/* Rendered Content */}
          <div className="prose max-w-none">
            <ContentRenderer result={selectedResult} />
          </div>

          {/* Copy Buttons */}
          <div className="mt-6 flex gap-3">
            <button
              onClick={handleCopyJson}
              className="flex-1 py-2 px-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Copy JSON
            </button>
            <button
              onClick={handleCopyText}
              className="flex-1 py-2 px-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Copy Text
            </button>
          </div>
        </div>
      )}
    </motion.div>
  )
}

export const ResultsPanel = React.memo(ResultsPanelComponent)
