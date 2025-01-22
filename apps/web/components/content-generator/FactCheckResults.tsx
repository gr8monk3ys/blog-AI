'use client'

import { useState } from 'react'
import type { FactCheckResult, ClaimVerification, VerificationStatus } from '../../types/factCheck'

interface FactCheckResultsProps {
  result: FactCheckResult
}

const STATUS_CONFIG: Record<
  VerificationStatus,
  { color: string; dotColor: string; label: string }
> = {
  verified: {
    color: 'text-emerald-700 dark:text-emerald-400',
    dotColor: 'bg-emerald-500',
    label: 'Verified',
  },
  unverified: {
    color: 'text-amber-700 dark:text-amber-400',
    dotColor: 'bg-amber-500',
    label: 'Unverified',
  },
  contradicted: {
    color: 'text-red-700 dark:text-red-400',
    dotColor: 'bg-red-500',
    label: 'Contradicted',
  },
}

function ConfidenceBar({ confidence }: { confidence: number }) {
  const percent = Math.round(confidence * 100)
  const barColor =
    percent >= 70 ? 'bg-emerald-500' : percent >= 40 ? 'bg-amber-500' : 'bg-red-500'

  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${barColor}`}
          style={{ width: `${percent}%` }}
        />
      </div>
      <span className="text-xs font-medium text-gray-500 dark:text-gray-400 w-8 text-right">
        {percent}%
      </span>
    </div>
  )
}

function ClaimRow({ claim, index }: { claim: ClaimVerification; index: number }) {
  const [expanded, setExpanded] = useState(false)
  const config = STATUS_CONFIG[claim.status]

  return (
    <div className="border-t border-black/[0.04] dark:border-white/[0.04] first:border-t-0">
      <button
        type="button"
        onClick={() => setExpanded((prev) => !prev)}
        className="w-full text-left px-5 py-3 flex items-start gap-3 hover:bg-black/[0.02] dark:hover:bg-white/[0.02] transition-colors"
        aria-expanded={expanded}
        aria-controls={`claim-detail-${index}`}
      >
        <span
          className={`mt-0.5 flex-shrink-0 text-xs font-semibold uppercase tracking-wide ${config.color}`}
        >
          {config.label}
        </span>
        <span className="flex-1 text-sm text-gray-700 dark:text-gray-300 leading-snug">
          {claim.text}
        </span>
        <span className="flex-shrink-0 text-xs text-gray-400">
          {Math.round(claim.confidence * 100)}%
        </span>
      </button>

      {expanded && (
        <div
          id={`claim-detail-${index}`}
          className="px-5 pb-4 border-t border-black/[0.04] dark:border-white/[0.04]"
        >
          <div className="mt-3">
            <ConfidenceBar confidence={claim.confidence} />
          </div>
          {claim.explanation && (
            <p className="mt-2 text-xs text-gray-600 dark:text-gray-400 leading-relaxed">
              {claim.explanation}
            </p>
          )}
          {claim.supporting_sources.length > 0 && (
            <div className="mt-2">
              <p className="text-xs font-medium text-gray-500 dark:text-gray-400">Sources:</p>
              <ul className="mt-1 space-y-0.5">
                {claim.supporting_sources.map((src, sIdx) => (
                  <li key={sIdx} className="text-xs text-gray-500 dark:text-gray-400 truncate">
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
}

export default function FactCheckResults({ result }: FactCheckResultsProps) {
  const [panelOpen, setPanelOpen] = useState(false)

  const overallPercent = Math.round(result.overall_confidence * 100)
  const overallColor =
    overallPercent >= 70
      ? 'text-emerald-600 dark:text-emerald-400'
      : overallPercent >= 40
        ? 'text-amber-600 dark:text-amber-400'
        : 'text-red-600 dark:text-red-400'

  return (
    <div className="glass-panel rounded-2xl overflow-hidden">
      {/* Header / collapsed summary */}
      <button
        type="button"
        onClick={() => setPanelOpen((prev) => !prev)}
        className="w-full flex items-center justify-between px-6 py-4 hover:bg-black/[0.02] dark:hover:bg-white/[0.02] transition-colors"
        aria-expanded={panelOpen}
        aria-controls="fact-check-body"
      >
        <div className="flex items-center gap-3">
          <span className="text-sm font-semibold text-gray-900 dark:text-gray-100">
            Fact Check
          </span>
          <div className="flex items-center gap-3 text-xs text-gray-500 dark:text-gray-400">
            <span className="flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 inline-block" />
              {result.verified_count} verified
            </span>
            <span className="flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-500 inline-block" />
              {result.unverified_count} unverified
            </span>
            <span className="flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-red-500 inline-block" />
              {result.contradicted_count} contradicted
            </span>
          </div>
        </div>
        <div className="flex items-center gap-3 flex-shrink-0">
          <span className={`text-sm font-bold ${overallColor}`}>
            {overallPercent}% confident
          </span>
          <svg
            className={`w-4 h-4 text-gray-400 transition-transform ${panelOpen ? 'rotate-180' : ''}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
            aria-hidden="true"
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>

      {/* Expanded body */}
      {panelOpen && (
        <div
          id="fact-check-body"
          className="border-t border-black/[0.04] dark:border-white/[0.04]"
        >
          {/* Overall confidence bar */}
          <div className="px-6 py-4">
            <ConfidenceBar confidence={result.overall_confidence} />
            {result.summary && (
              <p className="mt-3 text-xs text-gray-500 dark:text-gray-400 italic">
                {result.summary}
              </p>
            )}
          </div>

          {/* Claims */}
          {result.claims.length > 0 && (
            <div className="border-t border-black/[0.04] dark:border-white/[0.04]">
              <p className="px-5 pt-3 pb-1 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">
                Claims ({result.claims.length})
              </p>
              {result.claims.map((claim, idx) => (
                <ClaimRow key={idx} claim={claim} index={idx} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
