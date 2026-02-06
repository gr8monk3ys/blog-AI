'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  CheckIcon,
  ClipboardDocumentIcon,
  SparklesIcon,
  BeakerIcon,
  DocumentTextIcon,
  ChevronDownIcon,
  ChevronUpIcon,
} from '@heroicons/react/24/outline'
import ContentScore, { ContentScoreResult } from './ContentScore'

export interface ContentVariation {
  id: string
  content: string
  label: string
  temperature: number
  prompt_style: string
  scores?: ContentScoreResult | null
}

interface VariationCompareProps {
  variations: ContentVariation[]
  isLoading?: boolean
  onSelect?: (variation: ContentVariation) => void
  selectedId?: string | null
}

function getStyleDescription(style: string): string {
  switch (style) {
    case 'standard':
      return 'Balanced approach'
    case 'creative':
      return 'More creative and engaging'
    case 'concise':
      return 'Direct and to the point'
    default:
      return style
  }
}

function getStyleIcon(style: string) {
  switch (style) {
    case 'standard':
      return DocumentTextIcon
    case 'creative':
      return SparklesIcon
    case 'concise':
      return BeakerIcon
    default:
      return DocumentTextIcon
  }
}

function VariationCard({
  variation,
  isSelected,
  onSelect,
  index,
}: {
  variation: ContentVariation
  isSelected: boolean
  onSelect: () => void
  index: number
}) {
  const [copied, setCopied] = useState(false)
  const [showScores, setShowScores] = useState(false)

  const handleCopy = async (e: React.MouseEvent) => {
    e.stopPropagation()
    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(variation.content)
      } else {
        const textArea = document.createElement('textarea')
        textArea.value = variation.content
        textArea.style.position = 'fixed'
        textArea.style.left = '-9999px'
        document.body.appendChild(textArea)
        textArea.focus()
        textArea.select()
        document.execCommand('copy')
        document.body.removeChild(textArea)
      }
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  const StyleIcon = getStyleIcon(variation.prompt_style)

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.1 }}
      className={`relative rounded-xl border-2 transition-all duration-200 ${
        isSelected
          ? 'border-amber-500 bg-amber-50/50 shadow-md'
          : 'border-gray-200 bg-white hover:border-gray-300 hover:shadow-sm'
      }`}
    >
      {/* Header */}
      <div className="p-4 border-b border-gray-100">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {/* Variation badge */}
            <span
              className={`inline-flex items-center justify-center w-8 h-8 rounded-full text-sm font-bold ${
                isSelected
                  ? 'bg-amber-600 text-white'
                  : 'bg-gray-100 text-gray-700'
              }`}
            >
              {variation.label}
            </span>
            <div>
              <div className="flex items-center gap-2">
                <StyleIcon className="w-4 h-4 text-gray-500" />
                <span className="text-sm font-medium text-gray-900">
                  {getStyleDescription(variation.prompt_style)}
                </span>
              </div>
              <span className="text-xs text-gray-500">
                Temperature: {variation.temperature.toFixed(1)}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Score badge */}
            {variation.scores && (
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  setShowScores(!showScores)
                }}
                className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium transition-colors ${
                  variation.scores.overall_level === 'excellent'
                    ? 'bg-emerald-100 text-emerald-700 hover:bg-emerald-200'
                    : variation.scores.overall_level === 'good'
                      ? 'bg-blue-100 text-blue-700 hover:bg-blue-200'
                      : variation.scores.overall_level === 'fair'
                        ? 'bg-amber-100 text-amber-700 hover:bg-amber-200'
                        : 'bg-red-100 text-red-700 hover:bg-red-200'
                }`}
              >
                Score: {Math.round(variation.scores.overall_score)}
                {showScores ? (
                  <ChevronUpIcon className="w-3 h-3" />
                ) : (
                  <ChevronDownIcon className="w-3 h-3" />
                )}
              </button>
            )}

            {/* Copy button */}
            <button
              onClick={handleCopy}
              className="p-1.5 rounded-md text-gray-500 hover:text-gray-700 hover:bg-gray-100 transition-colors"
              aria-label="Copy content"
            >
              {copied ? (
                <CheckIcon className="w-4 h-4 text-emerald-500" />
              ) : (
                <ClipboardDocumentIcon className="w-4 h-4" />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Score details */}
      <AnimatePresence>
        {showScores && variation.scores && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="border-b border-gray-100"
          >
            <div className="p-4">
              <ContentScore scores={variation.scores} showDetails={false} />
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Content preview */}
      <div className="p-4">
        <div
          className="text-sm text-gray-700 whitespace-pre-wrap max-h-64 overflow-y-auto prose prose-sm"
          style={{ wordBreak: 'break-word' }}
        >
          {variation.content.length > 500
            ? `${variation.content.substring(0, 500)}...`
            : variation.content}
        </div>
      </div>

      {/* Select button */}
      <div className="p-4 pt-0">
        <button
          onClick={onSelect}
          className={`w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg text-sm font-medium transition-all ${
            isSelected
              ? 'bg-amber-600 text-white shadow-sm'
              : 'bg-gray-100 text-gray-700 hover:bg-amber-50 hover:text-amber-700'
          }`}
        >
          {isSelected ? (
            <>
              <CheckIcon className="w-4 h-4" />
              Selected
            </>
          ) : (
            'Pick this one'
          )}
        </button>
      </div>

      {/* Selected indicator */}
      {isSelected && (
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          className="absolute -top-2 -right-2 w-6 h-6 bg-amber-600 rounded-full flex items-center justify-center shadow-md"
        >
          <CheckIcon className="w-4 h-4 text-white" />
        </motion.div>
      )}
    </motion.div>
  )
}

function LoadingSkeleton() {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-center py-4">
        <div className="flex items-center gap-3">
          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-amber-600" />
          <span className="text-sm text-gray-600">Generating variations...</span>
        </div>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {[1, 2].map((i) => (
          <div
            key={i}
            className="rounded-xl border border-gray-200 p-4 animate-pulse"
          >
            <div className="flex items-center gap-3 mb-4">
              <div className="w-8 h-8 bg-gray-200 rounded-full" />
              <div className="space-y-2">
                <div className="h-4 w-24 bg-gray-200 rounded" />
                <div className="h-3 w-20 bg-gray-100 rounded" />
              </div>
            </div>
            <div className="space-y-2">
              <div className="h-3 bg-gray-200 rounded w-full" />
              <div className="h-3 bg-gray-200 rounded w-4/5" />
              <div className="h-3 bg-gray-200 rounded w-3/4" />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default function VariationCompare({
  variations,
  isLoading = false,
  onSelect,
  selectedId,
}: VariationCompareProps) {
  const [internalSelectedId, setInternalSelectedId] = useState<string | null>(null)

  const effectiveSelectedId = selectedId ?? internalSelectedId

  const handleSelect = (variation: ContentVariation) => {
    setInternalSelectedId(variation.id)
    onSelect?.(variation)
  }

  if (isLoading) {
    return <LoadingSkeleton />
  }

  if (variations.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <BeakerIcon className="w-12 h-12 mx-auto mb-3 text-gray-400" />
        <p>No variations generated yet.</p>
        <p className="text-sm mt-1">Enable variations to compare different content styles.</p>
      </div>
    )
  }

  // Find best and selected variation scores for comparison
  const bestScore = Math.max(
    ...variations.map((v) => v.scores?.overall_score ?? 0)
  )

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <BeakerIcon className="w-5 h-5 text-amber-600" />
          <h3 className="font-semibold text-gray-900">
            Compare Variations ({variations.length})
          </h3>
        </div>
        {bestScore > 0 && (
          <span className="text-xs text-gray-500">
            Best score: {Math.round(bestScore)}
          </span>
        )}
      </div>

      {/* Variations grid */}
      <div
        className={`grid gap-4 ${
          variations.length === 2
            ? 'grid-cols-1 lg:grid-cols-2'
            : 'grid-cols-1 lg:grid-cols-3'
        }`}
      >
        {variations.map((variation, index) => (
          <VariationCard
            key={variation.id}
            variation={variation}
            isSelected={effectiveSelectedId === variation.id}
            onSelect={() => handleSelect(variation)}
            index={index}
          />
        ))}
      </div>

      {/* Selection hint */}
      {!effectiveSelectedId && (
        <p className="text-center text-sm text-gray-500">
          Click &quot;Pick this one&quot; to select your preferred version
        </p>
      )}
    </div>
  )
}
