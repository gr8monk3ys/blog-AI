'use client'

import { useState, useEffect, useCallback } from 'react'
import Link from 'next/link'
import SiteHeader from '../../components/SiteHeader'
import SiteFooter from '../../components/SiteFooter'
import { m, AnimatePresence } from 'framer-motion'
import {
  SparklesIcon,
  ClockIcon,
  StarIcon,
  DocumentTextIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline'
import HistoryCard from '../../components/history/HistoryCard'
import HistoryFilters from '../../components/history/HistoryFilters'
import { historyApi } from '../../lib/history-api'
import type { GeneratedContentItem, HistoryFilters as HistoryFiltersType } from '../../types/history'
import { useAuth } from '../../lib/clerk-ui'

function useHistoryPageView() {
  const [items, setItems] = useState<GeneratedContentItem[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filters, setFilters] = useState<HistoryFiltersType>({})
  const [stats, setStats] = useState<{
    total: number
    favorites: number
    byCategory: Record<string, number>
  }>({ total: 0, favorites: 0, byCategory: {} })
  const [hasMore, setHasMore] = useState(false)
  const [isLoadingMore, setIsLoadingMore] = useState(false)

  const { isSignedIn } = useAuth()
  const isAvailable = isSignedIn && historyApi.isAvailable()

  // Fetch history
  const fetchHistory = useCallback(
    async (append = false) => {
      if (!isAvailable) {
        setIsLoading(false)
        return
      }

      try {
        if (append) {
          setIsLoadingMore(true)
        } else {
          setIsLoading(true)
        }
        setError(null)

        const offset = append ? items.length : 0
        const response = await historyApi.getHistory({
          ...filters,
          limit: 20,
          offset,
        })

        if (append) {
          setItems((prev) => [...prev, ...response.items])
        } else {
          setItems(response.items)
        }
        setHasMore(response.has_more)
      } catch (err) {
        console.error('Failed to fetch history:', err)
        setError('Failed to load history. Please try again.')
      } finally {
        setIsLoading(false)
        setIsLoadingMore(false)
      }
    },
    [filters, isAvailable, items.length]
  )

  // Fetch stats
  const fetchStats = useCallback(async () => {
    if (!isAvailable) return

    try {
      const historyStats = await historyApi.getStats()
      setStats({
        total: historyStats.total_generations,
        favorites: historyStats.total_favorites,
        byCategory: historyStats.by_category,
      })
    } catch (err) {
      console.error('Failed to fetch stats:', err)
    }
  }, [isAvailable])

  // Initial load
  useEffect(() => {
    fetchHistory()
    fetchStats()
    // We want to refetch when auth becomes available (Clerk loads / user signs in).
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAvailable])

  // Refetch when filters change
  useEffect(() => {
    fetchHistory()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters])

  // Handle delete
  const handleDelete = useCallback(
    async (id: string) => {
      try {
        await historyApi.deleteGeneration(id)
        setItems((prev) => prev.filter((item) => item.id !== id))
        setStats((prev) => ({
          ...prev,
          total: Math.max(0, prev.total - 1),
        }))
      } catch (err) {
        console.error('Failed to delete:', err)
      }
    },
    []
  )

  // Handle favorite toggle
  const handleFavoriteToggle = useCallback(
    (id: string, newStatus: boolean) => {
      setItems((prev) =>
        prev.map((item) =>
          item.id === id ? { ...item, is_favorite: newStatus } : item
        )
      )
      setStats((prev) => ({
        ...prev,
        favorites: newStatus ? prev.favorites + 1 : Math.max(0, prev.favorites - 1),
      }))
    },
    []
  )

  // Load more
  const handleLoadMore = useCallback(() => {
    fetchHistory(true)
  }, [fetchHistory])

  return (
    <main className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-950 dark:to-gray-900">
      <SiteHeader />

      {/* Hero Section */}
      <section className="bg-gradient-to-r from-amber-600 to-amber-700 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-16">
          <m.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="text-center"
          >
            <div className="inline-flex items-center gap-2 mb-4">
              <ClockIcon className="w-8 h-8" aria-hidden="true" />
            </div>
            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-4">
              Content History
            </h1>
            <p className="text-lg sm:text-xl text-amber-100 max-w-2xl mx-auto">
              View, reuse, and manage all your previously generated content in one
              place.
            </p>

            {/* Quick stats */}
            {isAvailable && (
              <div className="mt-8 flex flex-wrap justify-center gap-8">
                <div className="text-center">
                  <div className="text-3xl font-bold">{stats.total}</div>
                  <div className="text-sm text-amber-200">Generations</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold flex items-center justify-center gap-1">
                    <StarIcon className="w-6 h-6" aria-hidden="true" />
                    {stats.favorites}
                  </div>
                  <div className="text-sm text-amber-200">Favorites</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold">
                    {Object.keys(stats.byCategory).length}
                  </div>
                  <div className="text-sm text-amber-200">Categories Used</div>
                </div>
              </div>
            )}
          </m.div>
        </div>
      </section>

      {/* Main Content */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
        {!isAvailable ? (
          /* Not Configured State */
          <m.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center py-16"
          >
            <ExclamationTriangleIcon className="w-16 h-16 mx-auto text-amber-500 mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
              Sign In Required
            </h2>
            <p className="text-gray-600 dark:text-gray-400 max-w-md mx-auto mb-6">
              Sign in to view and manage your saved generations.
            </p>
            <Link
              href="/sign-in"
              className="inline-flex items-center gap-2 px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 transition-colors"
            >
              <DocumentTextIcon className="w-5 h-5" />
              Sign In
            </Link>
          </m.div>
        ) : (
          <>
            {/* Filters */}
            <m.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="mb-8"
            >
              <HistoryFilters
                filters={filters}
                onFiltersChange={setFilters}
                stats={stats}
              />
            </m.div>

            {/* Error State */}
            <AnimatePresence>
              {error && (
                <m.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl text-red-700 dark:text-red-400 text-sm"
                  role="alert"
                >
                  {error}
                </m.div>
              )}
            </AnimatePresence>

            {/* Loading State */}
            {isLoading ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {[1, 2, 3, 4, 5, 6].map((slot) => (
                  <div
                    key={`history-skeleton-${slot}`}
                    className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-5 animate-pulse"
                  >
                    <div className="flex items-start gap-3 mb-3">
                      <div className="w-10 h-10 rounded-lg bg-gray-200 dark:bg-gray-700" />
                      <div className="flex-1">
                        <div className="h-5 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-2" />
                        <div className="h-4 bg-gray-100 dark:bg-gray-800 rounded w-1/2" />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <div className="h-4 bg-gray-100 dark:bg-gray-800 rounded" />
                      <div className="h-4 bg-gray-100 dark:bg-gray-800 rounded w-5/6" />
                      <div className="h-4 bg-gray-100 dark:bg-gray-800 rounded w-4/6" />
                    </div>
                  </div>
                ))}
              </div>
            ) : items.length === 0 ? (
              /* Empty State */
              <m.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-center py-16"
              >
                <DocumentTextIcon className="w-16 h-16 mx-auto text-gray-300 dark:text-gray-600 mb-4" />
                <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
                  {filters.favorites_only
                    ? 'No Favorites Yet'
                    : filters.search
                    ? 'No Results Found'
                    : 'No Content History'}
                </h2>
                <p className="text-gray-600 dark:text-gray-400 max-w-md mx-auto mb-6">
                  {filters.favorites_only
                    ? 'Star your favorite generations to find them here.'
                    : filters.search
                    ? 'Try adjusting your search or filters.'
                    : 'Generate some content using our AI tools to build your history.'}
                </p>
                <Link
                  href="/tools"
                  className="inline-flex items-center gap-2 px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 transition-colors"
                >
                  <SparklesIcon className="w-5 h-5" />
                  Start Creating
                </Link>
              </m.div>
            ) : (
              <>
                {/* History Grid */}
                <m.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: 0.3, delay: 0.2 }}
                  className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
                >
                  <AnimatePresence mode="popLayout">
                    {items.map((item, index) => (
                      <HistoryCard
                        key={item.id}
                        item={item}
                        index={index}
                        onDelete={handleDelete}
                        onFavoriteToggle={handleFavoriteToggle}
                      />
                    ))}
                  </AnimatePresence>
                </m.div>

                {/* Load More */}
                {hasMore && (
                  <div className="mt-8 text-center">
                    <button
                      type="button"
                      onClick={handleLoadMore}
                      disabled={isLoadingMore}
                      className="inline-flex items-center gap-2 px-6 py-3 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 hover:border-gray-300 dark:hover:border-gray-600 transition-all focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {isLoadingMore ? (
                        <>
                          <svg
                            className="animate-spin w-4 h-4"
                            xmlns="http://www.w3.org/2000/svg"
                            fill="none"
                            viewBox="0 0 24 24"
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
                              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                            />
                          </svg>
                          Loading...
                        </>
                      ) : (
                        'Load More'
                      )}
                    </button>
                  </div>
                )}
              </>
            )}
          </>
        )}
      </section>

      <SiteFooter />
    </main>
  )
}

export default function HistoryPageClient() {
  return useHistoryPageView()
}
