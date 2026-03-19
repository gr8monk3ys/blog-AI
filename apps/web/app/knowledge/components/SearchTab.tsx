'use client'

import { useCallback, useState } from 'react'
import { MagnifyingGlassIcon, XMarkIcon, ClockIcon } from '@heroicons/react/24/outline'
import { motion, AnimatePresence } from 'framer-motion'
import { apiFetch, API_ENDPOINTS } from '../../../lib/api'
import type { KBDocument, KBSearchResult, KBSearchResponse } from '../../../types/knowledge'
import DocumentDetailModal from './DocumentDetailModal'

interface SearchTabProps {
  documents: KBDocument[]
}

export default function SearchTab({ documents }: SearchTabProps) {
  const [query, setQuery] = useState('')
  const [topK, setTopK] = useState(5)
  const [minScore, setMinScore] = useState(0.7)
  const [results, setResults] = useState<KBSearchResult[]>([])
  const [searchTimeMs, setSearchTimeMs] = useState<number | null>(null)
  const [searching, setSearching] = useState(false)
  const [hasSearched, setHasSearched] = useState(false)

  // For document detail modal
  const [selectedDoc, setSelectedDoc] = useState<KBDocument | null>(null)
  const [matchedChunkIds, setMatchedChunkIds] = useState<Set<string>>(new Set())
  const [chunkScores, setChunkScores] = useState<Map<string, number>>(new Map())

  const handleSearch = useCallback(async () => {
    if (!query.trim()) return
    setSearching(true)
    setHasSearched(true)
    try {
      const data = await apiFetch<KBSearchResponse>(API_ENDPOINTS.knowledge.search, {
        method: 'POST',
        body: JSON.stringify({
          query: query.trim(),
          top_k: topK,
          min_score: minScore,
        }),
      })
      setResults(data.results)
      setSearchTimeMs(data.search_time_ms)
    } catch {
      setResults([])
      setSearchTimeMs(null)
    } finally {
      setSearching(false)
    }
  }, [query, topK, minScore])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleSearch()
  }

  const openDocDetail = (result: KBSearchResult) => {
    const doc = documents.find((d) => d.id === result.document_id)
    if (!doc) return

    // Collect all matched chunk IDs and scores for this document
    const docResults = results.filter((r) => r.document_id === result.document_id)
    const ids = new Set(docResults.map((r) => r.chunk_id))
    const scores = new Map(docResults.map((r) => [r.chunk_id, r.score]))

    setMatchedChunkIds(ids)
    setChunkScores(scores)
    setSelectedDoc(doc)
  }

  const scoreColor = (score: number) => {
    if (score >= 0.9) return 'bg-green-500'
    if (score >= 0.8) return 'bg-amber-500'
    return 'bg-gray-400'
  }

  return (
    <div className="space-y-4">
      {/* Search input */}
      <div className="space-y-3">
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
            <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" aria-hidden="true" />
          </div>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            className="block w-full pl-11 pr-10 py-3 border border-gray-200 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-amber-500 text-sm text-gray-900 dark:text-gray-100 transition-all"
            placeholder="Search your knowledge base..."
            aria-label="Search knowledge base"
          />
          <AnimatePresence>
            {query && (
              <motion.button
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                type="button"
                onClick={() => setQuery('')}
                className="absolute inset-y-0 right-0 pr-4 flex items-center text-gray-400 hover:text-gray-600 transition-colors"
                aria-label="Clear search"
              >
                <XMarkIcon className="h-5 w-5" />
              </motion.button>
            )}
          </AnimatePresence>
        </div>

        {/* Controls row */}
        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-2">
            <label htmlFor="topk" className="text-xs text-gray-500 dark:text-gray-400">
              Results:
            </label>
            <select
              id="topk"
              value={topK}
              onChange={(e) => setTopK(Number(e.target.value))}
              className="rounded-md border-gray-300 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-100 text-sm py-1 focus:border-amber-500 focus:ring-amber-500"
            >
              {[3, 5, 10, 20].map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </select>
          </div>
          <div className="flex items-center gap-2">
            <label htmlFor="minscore" className="text-xs text-gray-500 dark:text-gray-400">
              Min score: {minScore.toFixed(1)}
            </label>
            <input
              id="minscore"
              type="range"
              min="0.5"
              max="1.0"
              step="0.05"
              value={minScore}
              onChange={(e) => setMinScore(Number(e.target.value))}
              className="w-24 accent-amber-500"
            />
          </div>
          <button
            type="button"
            onClick={handleSearch}
            disabled={!query.trim() || searching}
            className="ml-auto px-4 py-2 text-sm font-medium text-white bg-amber-600 rounded-lg hover:bg-amber-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {searching ? 'Searching...' : 'Search'}
          </button>
        </div>
      </div>

      {/* Results */}
      {searchTimeMs != null && (
        <div className="flex items-center gap-1 text-xs text-gray-400">
          <ClockIcon className="h-3.5 w-3.5" />
          Found {results.length} result{results.length !== 1 ? 's' : ''} in{' '}
          {searchTimeMs.toFixed(0)}ms
        </div>
      )}

      {hasSearched && results.length === 0 && !searching && (
        <div className="text-center py-12 text-gray-400 dark:text-gray-500">
          <MagnifyingGlassIcon className="h-10 w-10 mx-auto mb-3 opacity-50" />
          <p>No results found. Try adjusting your query or lowering the minimum score.</p>
        </div>
      )}

      {!hasSearched && (
        <div className="text-center py-12 text-gray-400 dark:text-gray-500">
          <MagnifyingGlassIcon className="h-10 w-10 mx-auto mb-3 opacity-50" />
          <p>Enter a query and press Enter or click Search to find relevant content.</p>
        </div>
      )}

      {results.length > 0 && (
        <div className="space-y-3">
          {results.map((result, idx) => (
            <div
              key={`${result.chunk_id}-${idx}`}
              className="rounded-lg border border-gray-200 dark:border-gray-700 p-4 bg-white dark:bg-gray-800/50"
            >
              <div className="flex items-start justify-between gap-3 mb-2">
                <button
                  type="button"
                  onClick={() => openDocDetail(result)}
                  className="text-sm font-medium text-amber-600 hover:text-amber-700 dark:text-amber-400 dark:hover:text-amber-300 text-left"
                >
                  {result.document_title}
                </button>
                <div className="flex items-center gap-2 flex-shrink-0">
                  {/* Score bar */}
                  <div className="w-16 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${scoreColor(result.score)}`}
                      style={{ width: `${result.score * 100}%` }}
                    />
                  </div>
                  <span className="text-xs text-gray-500 font-medium w-10 text-right">
                    {(result.score * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
              <p className="text-sm text-gray-700 dark:text-gray-300 line-clamp-3">
                {result.content}
              </p>
              {(result.page_number != null || result.section_title) && (
                <div className="flex items-center gap-2 mt-2 text-xs text-gray-400">
                  {result.page_number != null && <span>Page {result.page_number}</span>}
                  {result.section_title && <span>{result.section_title}</span>}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      <DocumentDetailModal
        document={selectedDoc}
        isOpen={selectedDoc !== null}
        onClose={() => setSelectedDoc(null)}
        onDelete={() => setSelectedDoc(null)}
        matchedChunkIds={matchedChunkIds}
        chunkScores={chunkScores}
      />
    </div>
  )
}
