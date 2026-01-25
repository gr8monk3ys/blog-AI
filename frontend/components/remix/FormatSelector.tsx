'use client'

import React from 'react'
import { motion } from 'framer-motion'
import type {
  ContentFormatId,
  ContentFormatInfo,
  RemixPreviewResponse,
} from '@/types/remix'

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

interface FormatSelectorProps {
  formats: ContentFormatInfo[]
  selectedFormats: ContentFormatId[]
  previews: Map<ContentFormatId, RemixPreviewResponse>
  isTransforming: boolean
  onToggleFormat: (formatId: ContentFormatId) => void
  onTransform: () => void
}

function FormatSelectorComponent({
  formats,
  selectedFormats,
  previews,
  isTransforming,
  onToggleFormat,
  onTransform,
}: FormatSelectorProps) {
  return (
    <div className="bg-white rounded-xl shadow-sm p-6">
      <h2 className="text-lg font-semibold mb-4">
        Select Target Formats
        <span className="text-sm font-normal text-gray-500 ml-2">
          ({selectedFormats.length}/6 selected)
        </span>
      </h2>

      <div className="grid grid-cols-2 gap-3">
        {formats.map((format) => {
          const isSelected = selectedFormats.includes(format.format)
          const preview = previews.get(format.format)

          return (
            <motion.button
              key={format.format}
              onClick={() => onToggleFormat(format.format)}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className={`p-4 rounded-lg text-left transition-all ${
                isSelected
                  ? 'bg-blue-50 border-2 border-blue-500'
                  : 'bg-gray-50 border-2 border-transparent hover:border-gray-200'
              }`}
            >
              <div className="flex items-center gap-2">
                <span className="text-2xl">
                  {FORMAT_ICONS[format.format] || '(doc)'}
                </span>
                <div>
                  <p className="font-medium">{format.name}</p>
                  <p className="text-xs text-gray-500">{format.platform}</p>
                </div>
              </div>
              {preview && (
                <p className="mt-2 text-xs text-gray-600 line-clamp-2">
                  {preview.sample_hook}
                </p>
              )}
            </motion.button>
          )
        })}
      </div>

      <button
        onClick={onTransform}
        disabled={isTransforming || selectedFormats.length === 0}
        className="w-full mt-6 py-3 px-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors font-medium"
      >
        {isTransforming ? (
          <span className="flex items-center justify-center gap-2">
            <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
                fill="none"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
              />
            </svg>
            Transforming...
          </span>
        ) : (
          `Remix to ${selectedFormats.length} Format${selectedFormats.length !== 1 ? 's' : ''}`
        )}
      </button>
    </div>
  )
}

export const FormatSelector = React.memo(FormatSelectorComponent)
