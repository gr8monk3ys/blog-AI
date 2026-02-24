'use client'

import { useState } from 'react'
import type { FactCheckResult, VerificationStatus } from '../../types/factCheck'

interface FactCheckPanelProps {
  result: FactCheckResult
}

const STATUS_CONFIG: Record<VerificationStatus, { label: string; color: string; bg: string }> = {
  verified: {
    label: 'Verified',
    color: 'text-emerald-700 dark:text-emerald-400',
    bg: 'bg-emerald-100 dark:bg-emerald-900/30',
  },
  unverified: {
    label: 'Unverified',
    color: 'text-amber-700 dark:text-amber-400',
    bg: 'bg-amber-100 dark:bg-amber-900/30',
  },
  contradicted: {
    label: 'Contradicted',
    color: 'text-red-700 dark:text-red-400',
    bg: 'bg-red-100 dark:bg-red-900/30',
  },
}

function ConfidenceBar({ confidence }: { confidence: number }) {
  const percent = Math.round(confidence * 100)
  const color =
    percent >= 70
      ? 'bg-emerald-500'
      : percent >= 40
        ? 'bg-amber-500'
        : 'bg-red-500'

  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${color}`}
          style={{ width: `${percent}%` }}
        />
      </div>
      <span className="text-xs font-medium text-gray-600 dark:text-gray-400 w-8 text-right">
        {percent}%
      </span>
    </div>
  )
}

export default function FactCheckPanel({ result }: FactCheckPanelProps) {
  const [expandedClaim, setExpandedClaim] = useState<number | null>(null)

  const overallPercent = Math.round(result.overall_confidence * 100)
  const overallColor =
    overallPercent >= 70
      ? 'text-emerald-600 dark:text-emerald-400'
      : overallPercent >= 40
        ? 'text-amber-600 dark:text-amber-400'
        : 'text-red-600 dark:text-red-400'

  return (
    <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-lg p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
          Fact Check
        </h3>
        <span className={`text-lg font-bold ${overallColor}`}>
          {overallPercent}% confident
        </span>
      </div>

      {/* Summary stats */}
      <div className="flex gap-4 mb-4">
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-emerald-500" />
          <span className="text-xs text-gray-600 dark:text-gray-400">
            {result.verified_count} verified
          </span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-amber-500" />
          <span className="text-xs text-gray-600 dark:text-gray-400">
            {result.unverified_count} unverified
          </span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-red-500" />
          <span className="text-xs text-gray-600 dark:text-gray-400">
            {result.contradicted_count} contradicted
          </span>
        </div>
      </div>

      {/* Overall confidence bar */}
      <div className="mb-5">
        <ConfidenceBar confidence={result.overall_confidence} />
      </div>

      {/* Claims list */}
      {result.claims.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">
            Claims ({result.claims.length})
          </h4>
          {result.claims.map((claim, idx) => {
            const config = STATUS_CONFIG[claim.status]
            const isExpanded = expandedClaim === idx

            return (
              <div
                key={idx}
                className="border border-gray-100 dark:border-gray-800 rounded-lg overflow-hidden"
              >
                <button
                  type="button"
                  onClick={() => setExpandedClaim(isExpanded ? null : idx)}
                  className="w-full text-left px-3 py-2.5 flex items-start gap-3 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
                >
                  <span
                    className={`inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium flex-shrink-0 mt-0.5 ${config.bg} ${config.color}`}
                  >
                    {config.label}
                  </span>
                  <span className="text-sm text-gray-700 dark:text-gray-300 flex-1 line-clamp-2">
                    {claim.text}
                  </span>
                  <span className="text-xs text-gray-400 flex-shrink-0">
                    {Math.round(claim.confidence * 100)}%
                  </span>
                </button>

                {isExpanded && (
                  <div className="px-3 pb-3 border-t border-gray-100 dark:border-gray-800">
                    <div className="mt-2">
                      <ConfidenceBar confidence={claim.confidence} />
                    </div>
                    {claim.explanation && (
                      <p className="mt-2 text-xs text-gray-600 dark:text-gray-400">
                        {claim.explanation}
                      </p>
                    )}
                    {claim.supporting_sources.length > 0 && (
                      <div className="mt-2">
                        <p className="text-xs font-medium text-gray-500 dark:text-gray-400">
                          Sources:
                        </p>
                        <ul className="mt-1 space-y-0.5">
                          {claim.supporting_sources.map((src, sIdx) => (
                            <li
                              key={sIdx}
                              className="text-xs text-gray-500 dark:text-gray-400 truncate"
                            >
                              {src}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}

      {/* Summary */}
      {result.summary && (
        <p className="mt-4 text-xs text-gray-500 dark:text-gray-400 italic">
          {result.summary}
        </p>
      )}
    </div>
  )
}
