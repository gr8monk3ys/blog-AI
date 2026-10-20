'use client'

import { useState, useEffect, useCallback } from 'react'
import Link from 'next/link'
import HistoryCard from '../../../components/history/HistoryCard'
import HistoryFilters from '../../../components/history/HistoryFilters'
import PageHeader from '../../../components/app/PageHeader'
import EmptyState from '../../../components/app/EmptyState'
import { Button, buttonVariants } from '../../../components/ui/Button'
import { historyApi } from '../../../lib/history-api'
import type { GeneratedContentItem, HistoryFilters as HistoryFiltersType } from '../../../types/history'
import { useAuth } from '../../../lib/clerk-ui'

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
    // Keyed on `filters` only; fetchHistory is a stable closure and including
    // it would re-run the effect on every render.
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

  const figures = [
    { label: 'Generations', value: stats.total },
    { label: 'Favorites', value: stats.favorites },
    { label: 'Categories used', value: Object.keys(stats.byCategory).length },
  ]

  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader
        kicker="Library"
        title="Content History"
        description="View, reuse, and manage all your previously generated content in one place."
      />

      {!isAvailable ? (
        <EmptyState
          kicker="History"
          title="Sign in required"
          description="Sign in to view and manage your saved generations."
          action={
            <Link href="/sign-in" className={buttonVariants()}>
              Sign In
            </Link>
          }
        />
      ) : (
        <>
          {/* Figures: mono, tabular, each introduced by its wall label. */}
          <dl className="mb-8 grid grid-cols-3 gap-4 border-y border-border py-4">
            {figures.map((figure) => (
              <div key={figure.label}>
                <dt className="label-mono">{figure.label}</dt>
                <dd className="mt-1 font-mono text-2xl tabular-nums text-foreground">{figure.value}</dd>
              </div>
            ))}
          </dl>

          <div className="mb-6">
            <HistoryFilters filters={filters} onFiltersChange={setFilters} stats={stats} />
          </div>

          {error && (
            <div
              className="mb-6 rounded-lg border border-destructive/30 bg-destructive-muted p-4 text-sm text-destructive"
              role="alert"
            >
              {error}
            </div>
          )}

          {isLoading ? (
            <ul className="divide-y divide-border" aria-busy="true" aria-label="Loading history">
              {[1, 2, 3, 4, 5].map((slot) => (
                <li key={`history-skeleton-${slot}`} className="animate-pulse py-5">
                  <div className="h-3 w-40 rounded-sm bg-muted" />
                  <div className="mt-3 h-4 w-3/4 rounded-sm bg-muted" />
                  <div className="mt-2 h-3 w-5/6 rounded-sm bg-muted" />
                  <div className="mt-1.5 h-3 w-2/3 rounded-sm bg-muted" />
                </li>
              ))}
            </ul>
          ) : items.length === 0 ? (
            <EmptyState
              kicker={filters.favorites_only ? 'Favorites' : filters.search ? 'Search' : 'History'}
              title={
                filters.favorites_only
                  ? 'No favorites yet'
                  : filters.search
                    ? 'No results found'
                    : 'No content history'
              }
              description={
                filters.favorites_only
                  ? 'Star your favorite generations to find them here.'
                  : filters.search
                    ? 'Try adjusting your search or filters.'
                    : 'Generate some content using our AI tools to build your history.'
              }
              action={
                filters.favorites_only || filters.search ? null : (
                  <Link href="/tools" className={buttonVariants()}>
                    Start Creating
                  </Link>
                )
              }
            />
          ) : (
            <>
              <ul className="divide-y divide-border border-t border-border">
                {items.map((item) => (
                  <HistoryCard
                    key={item.id}
                    item={item}
                    onDelete={handleDelete}
                    onFavoriteToggle={handleFavoriteToggle}
                  />
                ))}
              </ul>

              {hasMore && (
                <div className="mt-8 text-center">
                  <Button
                    type="button"
                    variant="secondary"
                    onClick={handleLoadMore}
                    disabled={isLoadingMore}
                  >
                    {isLoadingMore ? 'Loading…' : 'Load More'}
                  </Button>
                </div>
              )}
            </>
          )}
        </>
      )}
    </div>
  )
}

export default function HistoryPageClient() {
  return useHistoryPageView()
}
