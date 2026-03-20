'use client'

import { useState, useEffect, useCallback } from 'react'
import Link from 'next/link'
import { m, AnimatePresence } from 'framer-motion'
import { ArrowLeftIcon, ExclamationCircleIcon, SparklesIcon } from '@heroicons/react/24/outline'
import { API_ENDPOINTS, apiFetch, getDefaultHeaders } from '@/lib/api'
import ErrorBoundary from '@/components/ErrorBoundary'
import ScoreResult from '@/components/brand/ScoreResult'
import SiteHeader from '@/components/SiteHeader'
import SiteFooter from '@/components/SiteFooter'
import type { BrandProfile, VoiceScore, ContentType } from '@/types/brand'
import { SAMPLE_BRAND_PROFILES } from '@/types/brand'

const CONTENT_TYPES: { value: ContentType; label: string }[] = [
  { value: 'text', label: 'General Text' },
  { value: 'blog', label: 'Blog Post' },
  { value: 'email', label: 'Email' },
  { value: 'social', label: 'Social Media' },
  { value: 'website', label: 'Website Copy' },
  { value: 'article', label: 'Article' },
]

async function fetchActiveBrandProfiles(): Promise<BrandProfile[]> {
  try {
    const response = await fetch('/api/brand-profiles?activeOnly=true', {
      headers: await getDefaultHeaders(),
    })
    const data = await response.json().catch(() => ({}))
    if (data?.success && Array.isArray(data?.data)) {
      return data.data
    }
  } catch {
    // Ignore and fall back to samples
  }
  return SAMPLE_BRAND_PROFILES
}

interface ScoreResponse {
  success: boolean
  score: VoiceScore
  grade: string
  passed: boolean
}

function useScorePage() {
  const [profiles, setProfiles] = useState<BrandProfile[]>([])
  const [loadingProfiles, setLoadingProfiles] = useState(true)
  const [selectedProfileId, setSelectedProfileId] = useState<string>('')
  const [content, setContent] = useState<string>('')
  const [contentType, setContentType] = useState<ContentType>('text')
  const [isScoring, setIsScoring] = useState(false)
  const [scoreResponse, setScoreResponse] = useState<ScoreResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  // Load profiles on mount
  useEffect(() => {
    let mounted = true

    const load = async () => {
      setLoadingProfiles(true)
      const loaded = await fetchActiveBrandProfiles()
      if (!mounted) return
      setProfiles(loaded)
      const defaultProfile = loaded.find((p) => p.isDefault) ?? loaded[0]
      if (defaultProfile?.id) {
        setSelectedProfileId(defaultProfile.id)
      }
      setLoadingProfiles(false)
    }

    load()
    return () => {
      mounted = false
    }
  }, [])

  const handleScore = useCallback(async () => {
    if (!selectedProfileId || !content.trim()) return

    setIsScoring(true)
    setError(null)
    setScoreResponse(null)

    try {
      const response = await apiFetch<ScoreResponse>(API_ENDPOINTS.brandVoice.score, {
        method: 'POST',
        body: JSON.stringify({
          profile_id: selectedProfileId,
          content: content.trim(),
          content_type: contentType,
        }),
      })

      if (response.success) {
        setScoreResponse(response)
      } else {
        setError('Scoring did not return a result. Ensure this profile has been trained.')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Scoring failed. Please try again.')
    } finally {
      setIsScoring(false)
    }
  }, [selectedProfileId, content, contentType])

  const selectedProfile = profiles.find((p) => p.id === selectedProfileId) ?? null
  const canScore = !!selectedProfileId && content.trim().length > 0 && !isScoring

  return (
    <main className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-950 dark:to-gray-900">
      <SiteHeader />

      {/* Hero */}
      <section className="bg-gradient-to-r from-amber-600 to-amber-700 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-16">
          <m.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="text-center"
          >
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-white/10 mb-6">
              <SparklesIcon className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-4">
              Score Your Content
            </h1>
            <p className="text-lg sm:text-xl text-amber-100 max-w-2xl mx-auto">
              Measure how well your content matches your trained brand voice profile and get
              actionable suggestions to improve alignment.
            </p>
          </m.div>
        </div>
      </section>

      {/* Main content */}
      <section className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
        {/* Back link */}
        <div className="mb-6">
          <Link
            href="/brand"
            className="inline-flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 transition-colors"
          >
            <ArrowLeftIcon className="w-4 h-4" />
            Back to Brand Profiles
          </Link>
        </div>

        {/* Error banner */}
        <AnimatePresence>
          {error && (
            <m.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="mb-6 p-4 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-xl text-red-700 dark:text-red-400 flex items-start gap-3"
            >
              <ExclamationCircleIcon className="w-5 h-5 shrink-0 mt-0.5" />
              <span className="flex-1 text-sm">{error}</span>
              <button
                type="button"
                onClick={() => setError(null)}
                className="text-red-400 hover:text-red-600 dark:hover:text-red-300 shrink-0"
                aria-label="Dismiss error"
              >
                &times;
              </button>
            </m.div>
          )}
        </AnimatePresence>

        {/* Scoring card */}
        <m.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="glass-card rounded-2xl p-6 sm:p-8 border border-black/[0.08] dark:border-white/[0.08] bg-white/70 dark:bg-gray-800/70 backdrop-blur-sm shadow-sm"
        >
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-6">
            Scoring Configuration
          </h2>

          <div className="space-y-5">
            {/* Profile selector */}
            <div>
              <label
                htmlFor="profile-select"
                className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5"
              >
                Brand Profile
              </label>
              {loadingProfiles ? (
                <div className="h-10 rounded-xl bg-gray-200 dark:bg-gray-700 animate-pulse" />
              ) : (
                <select
                  id="profile-select"
                  value={selectedProfileId}
                  onChange={(e) => {
                    setSelectedProfileId(e.target.value)
                    setScoreResponse(null)
                  }}
                  className="w-full rounded-xl border-black/[0.08] dark:border-white/[0.08] bg-white/70 dark:bg-gray-800/70 backdrop-blur-sm border px-4 py-2.5 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-amber-500"
                >
                  <option value="">Select a profile…</option>
                  {profiles.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name}
                      {p.isDefault ? ' (Default)' : ''}
                    </option>
                  ))}
                </select>
              )}
              {!loadingProfiles && profiles.length === 0 && (
                <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
                  No profiles found.{' '}
                  <Link href="/brand" className="text-amber-600 hover:underline">
                    Create one
                  </Link>{' '}
                  first.
                </p>
              )}
              {selectedProfile && (
                <p className="mt-1.5 text-xs text-gray-500 dark:text-gray-400">
                  {selectedProfile.writingStyle} style &bull;{' '}
                  {selectedProfile.toneKeywords.slice(0, 3).join(', ')}
                </p>
              )}
            </div>

            {/* Content type selector */}
            <div>
              <label
                htmlFor="content-type-select"
                className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5"
              >
                Content Type
              </label>
              <select
                id="content-type-select"
                value={contentType}
                onChange={(e) => setContentType(e.target.value as ContentType)}
                className="w-full rounded-xl border-black/[0.08] dark:border-white/[0.08] bg-white/70 dark:bg-gray-800/70 backdrop-blur-sm border px-4 py-2.5 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-amber-500"
              >
                {CONTENT_TYPES.map((ct) => (
                  <option key={ct.value} value={ct.value}>
                    {ct.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Content textarea */}
            <div>
              <label
                htmlFor="content-textarea"
                className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5"
              >
                Content to Score
              </label>
              <textarea
                id="content-textarea"
                value={content}
                onChange={(e) => {
                  setContent(e.target.value)
                  setScoreResponse(null)
                }}
                placeholder="Paste the content you want to score against your brand voice…"
                rows={8}
                className="w-full rounded-xl border-black/[0.08] dark:border-white/[0.08] bg-white/70 dark:bg-gray-800/70 backdrop-blur-sm border px-4 py-3 text-sm text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 resize-none focus:outline-none focus:ring-2 focus:ring-amber-500"
              />
              <p className="mt-1.5 text-xs text-gray-400 dark:text-gray-500 text-right">
                {content.trim().split(/\s+/).filter(Boolean).length} words
              </p>
            </div>

            {/* Submit */}
            <button
              type="button"
              onClick={handleScore}
              disabled={!canScore}
              className="w-full py-3 px-6 rounded-xl bg-amber-600 hover:bg-amber-700 disabled:bg-gray-300 dark:disabled:bg-gray-700 text-white font-medium text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2"
            >
              {isScoring ? (
                <span className="inline-flex items-center gap-2">
                  <svg
                    className="animate-spin h-4 w-4 text-white"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                    aria-hidden="true"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                    />
                  </svg>
                  Scoring…
                </span>
              ) : (
                'Score Content'
              )}
            </button>
          </div>

          {/* Results */}
          <AnimatePresence>
            {scoreResponse && (
              <m.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="mt-6 pt-6 border-t border-black/[0.06] dark:border-white/[0.06]"
              >
                {/* Grade badge */}
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wide">
                    Results
                  </h3>
                  <div className="flex items-center gap-3">
                    <span
                      className={`text-xs font-bold px-2.5 py-1 rounded-full ${
                        scoreResponse.passed
                          ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                          : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                      }`}
                    >
                      {scoreResponse.passed ? 'Passed' : 'Failed'}
                    </span>
                    <span className="text-sm font-bold text-amber-600 dark:text-amber-400">
                      Grade: {scoreResponse.grade}
                    </span>
                  </div>
                </div>

                <ScoreResult score={scoreResponse.score} />
              </m.div>
            )}
          </AnimatePresence>
        </m.div>

        {/* Tips callout */}
        <m.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.1 }}
          className="mt-6 rounded-2xl border border-amber-200 bg-amber-50/80 p-5 dark:border-amber-900/40 dark:bg-amber-950/30"
        >
          <h3 className="text-sm font-semibold text-amber-900 dark:text-amber-100 mb-1">
            Tip: Train first, then score
          </h3>
          <p className="text-sm text-amber-800 dark:text-amber-200">
            For accurate results, make sure your brand profile has been trained with writing
            samples.{' '}
            <Link href="/brand/train" className="underline hover:no-underline">
              Go to Voice Training Studio
            </Link>{' '}
            to add samples and train your profile before scoring.
          </p>
        </m.div>
      </section>

      <SiteFooter />
    </main>
  )
}

export default function ScorePageClient() {
  return (
    <ErrorBoundary>
      {useScorePage()}
    </ErrorBoundary>
  )
}
