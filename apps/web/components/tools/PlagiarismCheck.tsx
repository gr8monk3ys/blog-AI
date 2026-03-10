'use client'

import type { PlagiarismCheckResult } from '../../types/plagiarism'

function riskStyles(level: string): { badge: string; label: string } {
  switch (level) {
    case 'none':
      return { badge: 'bg-emerald-100 text-emerald-700', label: 'None' }
    case 'low':
      return { badge: 'bg-emerald-100 text-emerald-700', label: 'Low' }
    case 'moderate':
      return { badge: 'bg-amber-100 text-amber-700', label: 'Moderate' }
    case 'high':
      return { badge: 'bg-orange-100 text-orange-700', label: 'High' }
    case 'critical':
      return { badge: 'bg-red-100 text-red-700', label: 'Critical' }
    default:
      return { badge: 'bg-gray-100 text-gray-700', label: String(level || 'Unknown') }
  }
}

export default function PlagiarismCheck({
  result,
  loading,
  error,
  onRun,
}: {
  result: PlagiarismCheckResult | null
  loading: boolean
  error: string | null
  onRun: (opts?: { skipCache?: boolean }) => void
}) {
  const risk = result ? riskStyles(result.risk_level) : null
  const sources = result?.matching_sources || []

  return (
    <div className="mt-4 bg-white rounded-xl border border-gray-200 p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-gray-900">Originality Check</p>
          <p className="text-xs text-gray-500">
            Scan for matching sources. Useful before publishing.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => onRun({ skipCache: false })}
            disabled={loading}
            className="inline-flex items-center px-3 py-1.5 rounded-lg text-xs font-medium bg-amber-600 text-white hover:bg-amber-700 disabled:bg-gray-300"
          >
            {loading ? 'Checking…' : result ? 'Re-check' : 'Check'}
          </button>
          {result && (
            <button
              type="button"
              onClick={() => onRun({ skipCache: true })}
              disabled={loading}
              className="inline-flex items-center px-3 py-1.5 rounded-lg text-xs font-medium bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 disabled:bg-gray-100"
              title="Skip cache and force a fresh check"
            >
              Fresh
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="mt-3 text-xs text-red-700 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
          {error}
        </div>
      )}

      {result && (
        <div className="mt-4 space-y-3">
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <span className={`px-2 py-0.5 rounded-full font-medium ${risk?.badge || ''}`}>
              Risk: {risk?.label}
            </span>
            <span className="px-2 py-0.5 rounded-full font-medium bg-gray-100 text-gray-700">
              Original: {Math.round(result.original_percentage)}%
            </span>
            <span className="px-2 py-0.5 rounded-full font-medium bg-gray-100 text-gray-700">
              Provider: {result.provider}
            </span>
            {result.cached && (
              <span className="px-2 py-0.5 rounded-full font-medium bg-gray-100 text-gray-700">
                Cached
              </span>
            )}
            <span className="text-gray-500">
              {(result.processing_time_ms / 1000).toFixed(1)}s
            </span>
          </div>

          {sources.length > 0 ? (
            <div>
              <p className="text-xs font-medium text-gray-700 mb-2">
                Matching sources
              </p>
              <div className="space-y-2">
                {sources.slice(0, 5).map((s) => (
                  <div
                    key={s.url}
                    className="rounded-lg border border-gray-200 p-3 text-xs"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0">
                        <a
                          href={s.url}
                          target="_blank"
                          rel="noreferrer"
                          className="block font-medium text-amber-700 hover:underline truncate"
                          title={s.title || s.url}
                        >
                          {s.title || s.url}
                        </a>
                        <p className="text-gray-500 truncate">{s.url}</p>
                      </div>
                      <span className="shrink-0 px-2 py-0.5 rounded-full bg-gray-100 text-gray-700 font-medium">
                        {Math.round(s.similarity_percentage)}%
                      </span>
                    </div>
                    {s.matched_text && (
                      <p className="mt-2 text-gray-600">
                        {s.matched_text}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <p className="text-xs text-gray-500">
              No matching sources returned.
            </p>
          )}
        </div>
      )}
    </div>
  )
}
