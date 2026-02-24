'use client'

import type { SEOScore } from '../../types/seo'

interface SEOScorePanelProps {
  score: SEOScore
}

const DIMENSIONS: { label: string; key: keyof SEOScore; thresholdDefault: number }[] = [
  { label: 'Topic Coverage', key: 'topic_coverage', thresholdDefault: 60 },
  { label: 'Term Usage', key: 'term_usage', thresholdDefault: 50 },
  { label: 'Structure', key: 'structure_score', thresholdDefault: 50 },
  { label: 'Readability', key: 'readability_score', thresholdDefault: 50 },
  { label: 'Word Count', key: 'word_count_score', thresholdDefault: 50 },
]

function scoreColor(score: number, threshold: number): string {
  if (score >= threshold) return 'text-emerald-600 dark:text-emerald-400'
  if (score >= threshold * 0.7) return 'text-amber-600 dark:text-amber-400'
  return 'text-red-600 dark:text-red-400'
}

function barColor(score: number, threshold: number): string {
  if (score >= threshold) return 'bg-emerald-500'
  if (score >= threshold * 0.7) return 'bg-amber-500'
  return 'bg-red-500'
}

function ringColor(passed: boolean): string {
  return passed
    ? 'stroke-emerald-500'
    : 'stroke-amber-500'
}

function RadialGauge({ score, passed }: { score: number; passed: boolean }) {
  const radius = 40
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (score / 100) * circumference

  return (
    <div className="relative flex items-center justify-center w-28 h-28">
      <svg className="w-28 h-28 -rotate-90" viewBox="0 0 100 100">
        <circle
          cx="50"
          cy="50"
          r={radius}
          fill="none"
          stroke="currentColor"
          className="text-gray-200 dark:text-gray-700"
          strokeWidth="8"
        />
        <circle
          cx="50"
          cy="50"
          r={radius}
          fill="none"
          className={ringColor(passed)}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
        />
      </svg>
      <div className="absolute flex flex-col items-center">
        <span className="text-2xl font-bold text-gray-900 dark:text-gray-100">
          {Math.round(score)}
        </span>
        <span className="text-xs text-gray-500 dark:text-gray-400">/ 100</span>
      </div>
    </div>
  )
}

export default function SEOScorePanel({ score }: SEOScorePanelProps) {
  return (
    <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-lg p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
          SEO Analysis
        </h3>
        <span
          className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
            score.passed
              ? 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400'
              : 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400'
          }`}
        >
          {score.passed ? 'Passed' : 'Needs Improvement'}
        </span>
      </div>

      <div className="flex items-start gap-6">
        {/* Radial gauge */}
        <div className="flex-shrink-0">
          <RadialGauge score={score.overall_score} passed={score.passed} />
          <p className="text-center text-xs text-gray-500 dark:text-gray-400 mt-1">
            {score.passes_used} pass{score.passes_used !== 1 ? 'es' : ''} &middot;{' '}
            {score.suggestions_applied} fix{score.suggestions_applied !== 1 ? 'es' : ''}
          </p>
        </div>

        {/* Dimension bars */}
        <div className="flex-1 space-y-3">
          {DIMENSIONS.map(({ label, key, thresholdDefault }) => {
            const value = score[key] as number
            return (
              <div key={key}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-medium text-gray-600 dark:text-gray-400">
                    {label}
                  </span>
                  <span className={`text-xs font-semibold ${scoreColor(value, thresholdDefault)}`}>
                    {Math.round(value)}
                  </span>
                </div>
                <div className="w-full h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${barColor(value, thresholdDefault)}`}
                    style={{ width: `${Math.min(value, 100)}%` }}
                  />
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
