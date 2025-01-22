'use client'

import { motion } from 'framer-motion'
import {
  CheckCircleIcon,
  ExclamationCircleIcon,
  ExclamationTriangleIcon,
  LightBulbIcon,
  ChevronDownIcon,
  ChevronUpIcon,
} from '@heroicons/react/24/outline'
import { useState } from 'react'

interface ScoreMetric {
  score: number
  level: 'excellent' | 'good' | 'fair' | 'poor'
  suggestions: string[]
}

interface ReadabilityScore extends ScoreMetric {
  flesch_kincaid_grade: number
  flesch_reading_ease: number
  average_sentence_length: number
  average_word_length: number
  complex_word_percentage: number
}

interface SEOScore extends ScoreMetric {
  keyword_density: number
  keyword_placement: Record<string, boolean>
  word_count: number
  heading_count: number
  has_meta_elements: boolean
  internal_link_potential: number
}

interface EngagementScore extends ScoreMetric {
  hook_strength: number
  cta_count: number
  emotional_word_count: number
  question_count: number
  list_count: number
  storytelling_elements: number
}

export interface ContentScoreResult {
  overall_score: number
  overall_level: 'excellent' | 'good' | 'fair' | 'poor'
  readability: ReadabilityScore
  seo: SEOScore
  engagement: EngagementScore
  summary: string
  top_improvements: string[]
}

interface ContentScoreProps {
  scores: ContentScoreResult
  isLoading?: boolean
  showDetails?: boolean
}

function getScoreColor(level: string): string {
  switch (level) {
    case 'excellent':
      return 'text-emerald-600'
    case 'good':
      return 'text-blue-600'
    case 'fair':
      return 'text-amber-600'
    case 'poor':
      return 'text-red-600'
    default:
      return 'text-gray-600'
  }
}

function getScoreBgColor(level: string): string {
  switch (level) {
    case 'excellent':
      return 'bg-emerald-100'
    case 'good':
      return 'bg-blue-100'
    case 'fair':
      return 'bg-amber-100'
    case 'poor':
      return 'bg-red-100'
    default:
      return 'bg-gray-100'
  }
}

function getScoreRingColor(level: string): string {
  switch (level) {
    case 'excellent':
      return 'stroke-emerald-500'
    case 'good':
      return 'stroke-blue-500'
    case 'fair':
      return 'stroke-amber-500'
    case 'poor':
      return 'stroke-red-500'
    default:
      return 'stroke-gray-400'
  }
}

function CircularProgress({
  score,
  level,
  size = 80,
  strokeWidth = 8,
  label,
}: {
  score: number
  level: string
  size?: number
  strokeWidth?: number
  label: string
}) {
  const radius = (size - strokeWidth) / 2
  const circumference = radius * 2 * Math.PI
  const offset = circumference - (score / 100) * circumference

  return (
    <div className="flex flex-col items-center">
      <div className="relative" style={{ width: size, height: size }}>
        {/* Background circle */}
        <svg className="transform -rotate-90" width={size} height={size}>
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            strokeWidth={strokeWidth}
            className="fill-none stroke-gray-200"
          />
          {/* Progress circle */}
          <motion.circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            strokeWidth={strokeWidth}
            className={`fill-none ${getScoreRingColor(level)}`}
            strokeLinecap="round"
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset: offset }}
            transition={{ duration: 1, ease: 'easeOut' }}
            style={{
              strokeDasharray: circumference,
            }}
          />
        </svg>
        {/* Score text */}
        <div className="absolute inset-0 flex items-center justify-center">
          <span className={`text-lg font-bold ${getScoreColor(level)}`}>
            {Math.round(score)}
          </span>
        </div>
      </div>
      <span className="mt-2 text-xs font-medium text-gray-600">{label}</span>
    </div>
  )
}

function ScoreIcon({ level }: { level: string }) {
  switch (level) {
    case 'excellent':
      return <CheckCircleIcon className="w-5 h-5 text-emerald-500" />
    case 'good':
      return <CheckCircleIcon className="w-5 h-5 text-blue-500" />
    case 'fair':
      return <ExclamationTriangleIcon className="w-5 h-5 text-amber-500" />
    case 'poor':
      return <ExclamationCircleIcon className="w-5 h-5 text-red-500" />
    default:
      return null
  }
}

function DetailSection({
  title,
  score,
  level,
  metrics,
  suggestions,
}: {
  title: string
  score: number
  level: string
  metrics: { label: string; value: string | number }[]
  suggestions: string[]
}) {
  const [isExpanded, setIsExpanded] = useState(false)

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-3 flex items-center justify-between bg-gray-50 hover:bg-gray-100 transition-colors"
      >
        <div className="flex items-center gap-3">
          <ScoreIcon level={level} />
          <span className="font-medium text-gray-900">{title}</span>
          <span
            className={`px-2 py-0.5 rounded-full text-xs font-medium ${getScoreBgColor(level)} ${getScoreColor(level)}`}
          >
            {Math.round(score)}/100
          </span>
        </div>
        {isExpanded ? (
          <ChevronUpIcon className="w-4 h-4 text-gray-500" />
        ) : (
          <ChevronDownIcon className="w-4 h-4 text-gray-500" />
        )}
      </button>

      {isExpanded && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          exit={{ opacity: 0, height: 0 }}
          className="px-4 py-3 bg-white"
        >
          {/* Metrics grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-4">
            {metrics.map((metric) => (
              <div key={metric.label} className="text-sm">
                <span className="text-gray-500">{metric.label}:</span>
                <span className="ml-1 font-medium text-gray-900">{metric.value}</span>
              </div>
            ))}
          </div>

          {/* Suggestions */}
          {suggestions.length > 0 && (
            <div className="border-t border-gray-100 pt-3">
              <div className="flex items-center gap-1.5 mb-2">
                <LightBulbIcon className="w-4 h-4 text-amber-500" />
                <span className="text-xs font-medium text-gray-700">Suggestions</span>
              </div>
              <ul className="space-y-1.5">
                {suggestions.map((suggestion, idx) => (
                  <li key={idx} className="text-sm text-gray-600 flex items-start gap-2">
                    <span className="text-amber-500 mt-0.5">-</span>
                    <span>{suggestion}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </motion.div>
      )}
    </div>
  )
}

export default function ContentScore({
  scores,
  isLoading = false,
  showDetails = true,
}: ContentScoreProps) {
  if (isLoading) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-600" />
          <span className="ml-3 text-sm text-gray-600">Analyzing content...</span>
        </div>
      </div>
    )
  }

  const readabilityMetrics = [
    { label: 'Grade Level', value: scores.readability.flesch_kincaid_grade },
    { label: 'Reading Ease', value: scores.readability.flesch_reading_ease },
    { label: 'Avg Sentence', value: `${scores.readability.average_sentence_length} words` },
    { label: 'Complex Words', value: `${scores.readability.complex_word_percentage}%` },
  ]

  const seoMetrics = [
    { label: 'Word Count', value: scores.seo.word_count },
    { label: 'Headings', value: scores.seo.heading_count },
    { label: 'Keyword Density', value: `${scores.seo.keyword_density}%` },
    { label: 'In Title', value: scores.seo.keyword_placement?.in_title ? 'Yes' : 'No' },
    { label: 'In First Para', value: scores.seo.keyword_placement?.in_first_paragraph ? 'Yes' : 'No' },
  ]

  const engagementMetrics = [
    { label: 'Hook Strength', value: `${scores.engagement.hook_strength}%` },
    { label: 'CTAs', value: scores.engagement.cta_count },
    { label: 'Power Words', value: scores.engagement.emotional_word_count },
    { label: 'Questions', value: scores.engagement.question_count },
    { label: 'Lists', value: scores.engagement.list_count },
  ]

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="bg-white rounded-xl border border-gray-200 overflow-hidden"
    >
      {/* Header with overall score */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-start justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Content Score</h3>
            <p className="mt-1 text-sm text-gray-600">{scores.summary}</p>
          </div>
          <CircularProgress
            score={scores.overall_score}
            level={scores.overall_level}
            size={70}
            strokeWidth={6}
            label="Overall"
          />
        </div>

        {/* Score breakdown circles */}
        <div className="flex justify-center gap-8 mt-6 pt-4 border-t border-gray-100">
          <CircularProgress
            score={scores.readability.score}
            level={scores.readability.level}
            size={60}
            strokeWidth={5}
            label="Readability"
          />
          <CircularProgress
            score={scores.seo.score}
            level={scores.seo.level}
            size={60}
            strokeWidth={5}
            label="SEO"
          />
          <CircularProgress
            score={scores.engagement.score}
            level={scores.engagement.level}
            size={60}
            strokeWidth={5}
            label="Engagement"
          />
        </div>
      </div>

      {/* Top improvements */}
      {scores.top_improvements && scores.top_improvements.length > 0 && (
        <div className="px-6 py-4 bg-amber-50 border-b border-amber-100">
          <div className="flex items-center gap-2 mb-2">
            <LightBulbIcon className="w-5 h-5 text-amber-600" />
            <span className="font-medium text-amber-900">Priority Improvements</span>
          </div>
          <ul className="space-y-1.5">
            {scores.top_improvements.map((improvement, idx) => (
              <li key={idx} className="text-sm text-amber-800 flex items-start gap-2">
                <span className="font-medium">{idx + 1}.</span>
                <span>{improvement}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Detailed sections */}
      {showDetails && (
        <div className="p-4 space-y-3">
          <DetailSection
            title="Readability"
            score={scores.readability.score}
            level={scores.readability.level}
            metrics={readabilityMetrics}
            suggestions={scores.readability.suggestions}
          />
          <DetailSection
            title="SEO"
            score={scores.seo.score}
            level={scores.seo.level}
            metrics={seoMetrics}
            suggestions={scores.seo.suggestions}
          />
          <DetailSection
            title="Engagement"
            score={scores.engagement.score}
            level={scores.engagement.level}
            metrics={engagementMetrics}
            suggestions={scores.engagement.suggestions}
          />
        </div>
      )}
    </motion.div>
  )
}
