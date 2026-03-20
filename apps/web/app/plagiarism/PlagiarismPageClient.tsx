'use client'

import { useState, useEffect } from 'react'
import { ShieldCheckIcon } from '@heroicons/react/24/outline'
import { API_ENDPOINTS, getDefaultHeaders } from '../../lib/api'
import { useToast } from '../../hooks/useToast'
import type {
  PlagiarismCheckResult,
  PlagiarismCheckResponse,
  PlagiarismProvider,
  PlagiarismQuotaResponse,
  ProviderQuota,
} from '../../types/plagiarism'

function riskStyles(level: string): { badge: string; label: string; gauge: string } {
  switch (level) {
    case 'none':
      return { badge: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300', label: 'None', gauge: 'bg-emerald-500' }
    case 'low':
      return { badge: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300', label: 'Low', gauge: 'bg-blue-500' }
    case 'moderate':
      return { badge: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300', label: 'Moderate', gauge: 'bg-amber-500' }
    case 'high':
      return { badge: 'bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-300', label: 'High', gauge: 'bg-orange-500' }
    case 'critical':
      return { badge: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300', label: 'Critical', gauge: 'bg-red-500' }
    default:
      return { badge: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300', label: String(level || 'Unknown'), gauge: 'bg-gray-400' }
  }
}

const PROVIDERS: { value: '' | PlagiarismProvider; label: string }[] = [
  { value: '', label: 'Auto (recommended)' },
  { value: 'copyscape', label: 'Copyscape' },
  { value: 'originality', label: 'Originality.ai' },
  { value: 'embedding', label: 'Embedding similarity' },
]

export default function PlagiarismPageClient() {
  const [content, setContent] = useState('')
  const [title, setTitle] = useState('')
  const [provider, setProvider] = useState<'' | PlagiarismProvider>('')
  const [excludeUrls, setExcludeUrls] = useState<string[]>([])
  const [excludeUrlInput, setExcludeUrlInput] = useState('')
  const [skipCache, setSkipCache] = useState(false)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<PlagiarismCheckResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [quota, setQuota] = useState<PlagiarismQuotaResponse | null>(null)
  const { showToast, ToastComponent } = useToast()

  useEffect(() => {
    fetchQuota()
  }, [])

  async function fetchQuota() {
    try {
      const headers = await getDefaultHeaders()
      const res = await fetch(API_ENDPOINTS.content.plagiarismQuota, { headers })
      if (res.ok) {
        const data: PlagiarismQuotaResponse = await res.json()
        setQuota(data)
      }
    } catch {
      // Quota fetch is non-critical
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (content.length < 50) {
      showToast({ message: 'Content must be at least 50 characters.', variant: 'warning' })
      return
    }

    setLoading(true)
    setError(null)

    try {
      const headers = await getDefaultHeaders()
      const body: Record<string, unknown> = { content, skip_cache: skipCache }
      if (title) body.title = title
      if (provider) body.provider = provider
      if (excludeUrls.length > 0) body.exclude_urls = excludeUrls

      const res = await fetch(API_ENDPOINTS.content.checkPlagiarism, {
        method: 'POST',
        headers,
        body: JSON.stringify(body),
      })

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}))
        throw new Error(errData?.detail || errData?.error || `HTTP ${res.status}`)
      }

      const data: PlagiarismCheckResponse = await res.json()
      if (data.success && data.data) {
        setResult(data.data)
        showToast({ message: 'Plagiarism check complete.', variant: 'success' })
        fetchQuota()
      } else {
        setError(data.error || 'Check failed.')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Plagiarism check failed.')
    } finally {
      setLoading(false)
    }
  }

  function addExcludeUrl() {
    const url = excludeUrlInput.trim()
    if (url && !excludeUrls.includes(url) && excludeUrls.length < 10) {
      setExcludeUrls([...excludeUrls, url])
      setExcludeUrlInput('')
    }
  }

  function removeExcludeUrl(url: string) {
    setExcludeUrls(excludeUrls.filter((u) => u !== url))
  }

  const risk = result ? riskStyles(result.risk_level) : null
  const sources = result?.matching_sources || []

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <div className="flex items-center gap-3 mb-8">
        <div className="inline-flex items-center justify-center w-11 h-11 rounded-xl bg-amber-100/80 dark:bg-amber-900/40 text-amber-700">
          <ShieldCheckIcon className="w-5 h-5" aria-hidden="true" />
        </div>
        <div>
          <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">Plagiarism Detection</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">Scan content for matching sources before publishing</p>
        </div>
      </div>

      {/* Quota display */}
      {quota && quota.providers.length > 0 && (
        <div className="mb-6 flex flex-wrap gap-3">
          {quota.providers.map((pq: ProviderQuota) => (
            <div
              key={pq.provider}
              className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium border ${
                pq.is_available
                  ? 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300'
                  : 'bg-gray-50 dark:bg-gray-900 border-gray-200 dark:border-gray-700 text-gray-400 dark:text-gray-500'
              }`}
            >
              <span className="capitalize">{pq.provider}</span>
              <span className="text-gray-400 dark:text-gray-500">
                {pq.remaining_credits} credits left
              </span>
              {pq.daily_limit > 0 && (
                <span className="text-gray-400 dark:text-gray-500">
                  ({pq.daily_used}/{pq.daily_limit} daily)
                </span>
              )}
            </div>
          ))}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Content textarea */}
        <div>
          <label htmlFor="plag-content" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
            Content to check <span className="text-red-500">*</span>
          </label>
          <textarea
            id="plag-content"
            rows={10}
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Paste the content you want to check for plagiarism (minimum 50 characters)..."
            className="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-4 py-3 text-sm text-gray-900 dark:text-gray-100 placeholder-gray-400 focus:border-amber-500 focus:ring-1 focus:ring-amber-500"
            required
            minLength={50}
          />
          <div className="mt-1 flex justify-between text-xs text-gray-400">
            <span>{content.length < 50 ? `${50 - content.length} more characters needed` : 'Ready to check'}</span>
            <span>{content.length.toLocaleString()} characters</span>
          </div>
        </div>

        {/* Optional fields */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label htmlFor="plag-title" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
              Title (optional)
            </label>
            <input
              id="plag-title"
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Content title"
              className="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-4 py-2.5 text-sm text-gray-900 dark:text-gray-100 placeholder-gray-400 focus:border-amber-500 focus:ring-1 focus:ring-amber-500"
            />
          </div>

          <div>
            <label htmlFor="plag-provider" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
              Provider
            </label>
            <select
              id="plag-provider"
              value={provider}
              onChange={(e) => setProvider(e.target.value as '' | PlagiarismProvider)}
              className="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-4 py-2.5 text-sm text-gray-900 dark:text-gray-100 focus:border-amber-500 focus:ring-1 focus:ring-amber-500"
            >
              {PROVIDERS.map((p) => (
                <option key={p.value} value={p.value}>{p.label}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Exclude URLs */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
            Exclude URLs (optional)
          </label>
          <div className="flex gap-2">
            <input
              type="url"
              value={excludeUrlInput}
              onChange={(e) => setExcludeUrlInput(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); addExcludeUrl() } }}
              placeholder="https://example.com/your-original"
              className="flex-1 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-4 py-2.5 text-sm text-gray-900 dark:text-gray-100 placeholder-gray-400 focus:border-amber-500 focus:ring-1 focus:ring-amber-500"
            />
            <button
              type="button"
              onClick={addExcludeUrl}
              disabled={excludeUrls.length >= 10}
              className="px-4 py-2.5 rounded-lg text-sm font-medium bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700 border border-gray-300 dark:border-gray-700 disabled:opacity-50"
            >
              Add
            </button>
          </div>
          {excludeUrls.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-2">
              {excludeUrls.map((url) => (
                <span
                  key={url}
                  className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 border border-gray-200 dark:border-gray-700"
                >
                  <span className="max-w-[200px] truncate">{url}</span>
                  <button type="button" onClick={() => removeExcludeUrl(url)} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">
                    &times;
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Skip cache toggle */}
        <label className="inline-flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 cursor-pointer">
          <input
            type="checkbox"
            checked={skipCache}
            onChange={(e) => setSkipCache(e.target.checked)}
            className="rounded border-gray-300 text-amber-600 focus:ring-amber-500"
          />
          Skip cache (force fresh check)
        </label>

        {/* Submit */}
        <button
          type="submit"
          disabled={loading || content.length < 50}
          className="inline-flex items-center gap-2 px-6 py-3 rounded-lg text-sm font-medium bg-amber-600 text-white hover:bg-amber-700 disabled:bg-gray-300 dark:disabled:bg-gray-700 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Checking...
            </>
          ) : (
            <>
              <ShieldCheckIcon className="w-4 h-4" />
              {result ? 'Re-check' : 'Check for Plagiarism'}
            </>
          )}
        </button>
      </form>

      {/* Error */}
      {error && (
        <div className="mt-6 rounded-lg border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20 px-4 py-3 text-sm text-red-700 dark:text-red-300">
          {error}
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="mt-8 space-y-6">
          {/* Score gauge */}
          <div className="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Results</h2>
              <span className={`px-3 py-1 rounded-full text-xs font-medium ${risk?.badge}`}>
                Risk: {risk?.label}
              </span>
            </div>

            {/* Score bar */}
            <div className="mb-4">
              <div className="flex justify-between text-sm mb-1.5">
                <span className="text-gray-600 dark:text-gray-400">Similarity Score</span>
                <span className="font-semibold text-gray-900 dark:text-gray-100">{Math.round(result.overall_score)}%</span>
              </div>
              <div className="h-3 rounded-full bg-gray-100 dark:bg-gray-700 overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${risk?.gauge}`}
                  style={{ width: `${Math.min(result.overall_score, 100)}%` }}
                />
              </div>
            </div>

            {/* Stats row */}
            <div className="flex flex-wrap gap-3 text-xs">
              <span className="px-2.5 py-1 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 font-medium">
                Original: {Math.round(result.original_percentage)}%
              </span>
              <span className="px-2.5 py-1 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 font-medium capitalize">
                Provider: {result.provider}
              </span>
              <span className="px-2.5 py-1 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 font-medium">
                {result.total_words_checked.toLocaleString()} words checked
              </span>
              {result.cached && (
                <span className="px-2.5 py-1 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 font-medium">
                  Cached
                </span>
              )}
              <span className="text-gray-400 dark:text-gray-500 self-center">
                {(result.processing_time_ms / 1000).toFixed(1)}s
              </span>
            </div>
          </div>

          {/* Matching sources */}
          {sources.length > 0 ? (
            <div className="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-6">
              <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-4">
                Matching Sources ({sources.length})
              </h3>
              <div className="space-y-3">
                {sources.map((s, i) => (
                  <div
                    key={`${s.url}-${i}`}
                    className="rounded-lg border border-gray-200 dark:border-gray-700 p-4"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0 flex-1">
                        <a
                          href={s.url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-sm font-medium text-amber-700 dark:text-amber-400 hover:underline block truncate"
                          title={s.title || s.url}
                        >
                          {s.title || s.url}
                        </a>
                        <p className="text-xs text-gray-500 dark:text-gray-400 truncate mt-0.5">{s.url}</p>
                      </div>
                      <span className="shrink-0 px-2.5 py-1 rounded-full bg-gray-100 dark:bg-gray-700 text-xs font-medium text-gray-700 dark:text-gray-300">
                        {Math.round(s.similarity_percentage)}%
                      </span>
                    </div>
                    {s.matched_text && (
                      <p className="mt-2 text-xs text-gray-600 dark:text-gray-400 leading-relaxed border-l-2 border-gray-200 dark:border-gray-600 pl-3">
                        {s.matched_text}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ) : (
            result.status === 'completed' && (
              <div className="rounded-xl border border-emerald-200 dark:border-emerald-800 bg-emerald-50 dark:bg-emerald-900/20 p-6 text-center">
                <p className="text-sm text-emerald-700 dark:text-emerald-300 font-medium">No matching sources found. Your content appears to be original.</p>
              </div>
            )
          )}
        </div>
      )}

      <ToastComponent />
    </div>
  )
}
