'use client'

import { useRef, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  MagnifyingGlassIcon,
  XMarkIcon,
  StarIcon,
  FunnelIcon,
} from '@heroicons/react/24/outline'
import { ToolCategory, TOOL_CATEGORIES } from '../../types/tools'
import type { HistoryFilters as HistoryFiltersType } from '../../types/history'

interface HistoryFiltersProps {
  filters: HistoryFiltersType
  onFiltersChange: (filters: HistoryFiltersType) => void
  stats?: {
    total: number
    favorites: number
    byCategory: Record<string, number>
  }
}

export default function HistoryFilters({
  filters,
  onFiltersChange,
  stats,
}: HistoryFiltersProps) {
  const searchInputRef = useRef<HTMLInputElement>(null)

  const categories: Array<{ id: ToolCategory | 'all'; name: string }> = [
    { id: 'all', name: 'All' },
    ...Object.values(TOOL_CATEGORIES).map((cat) => ({
      id: cat.id,
      name: cat.name,
    })),
  ]

  const handleSearchChange = useCallback(
    (value: string) => {
      onFiltersChange({ ...filters, search: value || undefined })
    },
    [filters, onFiltersChange]
  )

  const handleCategoryChange = useCallback(
    (category: ToolCategory | 'all') => {
      onFiltersChange({
        ...filters,
        category: category === 'all' ? undefined : category,
      })
    },
    [filters, onFiltersChange]
  )

  const handleFavoritesToggle = useCallback(() => {
    onFiltersChange({
      ...filters,
      favorites_only: !filters.favorites_only,
    })
  }, [filters, onFiltersChange])

  const clearSearch = useCallback(() => {
    onFiltersChange({ ...filters, search: undefined })
    searchInputRef.current?.focus()
  }, [filters, onFiltersChange])

  const clearAllFilters = useCallback(() => {
    onFiltersChange({})
  }, [onFiltersChange])

  const hasActiveFilters =
    filters.search ||
    filters.category ||
    filters.favorites_only ||
    filters.date_from ||
    filters.date_to

  const buttonRefs = useRef<(HTMLButtonElement | null)[]>([])

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent, index: number) => {
      let nextIndex: number | null = null

      if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
        e.preventDefault()
        nextIndex = (index + 1) % categories.length
      } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
        e.preventDefault()
        nextIndex = (index - 1 + categories.length) % categories.length
      } else if (e.key === 'Home') {
        e.preventDefault()
        nextIndex = 0
      } else if (e.key === 'End') {
        e.preventDefault()
        nextIndex = categories.length - 1
      }

      if (nextIndex !== null) {
        const nextCategory = categories[nextIndex]
        if (nextCategory) {
          buttonRefs.current[nextIndex]?.focus()
          handleCategoryChange(nextCategory.id)
        }
      }
    },
    [categories, handleCategoryChange]
  )

  const selectedCategory = filters.category || 'all'

  return (
    <div className="space-y-4">
      {/* Search and Quick Filters Row */}
      <div className="flex flex-col sm:flex-row gap-4">
        {/* Search */}
        <div className="relative flex-1">
          <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
            <MagnifyingGlassIcon
              className="h-5 w-5 text-gray-400"
              aria-hidden="true"
            />
          </div>
          <input
            ref={searchInputRef}
            type="text"
            value={filters.search || ''}
            onChange={(e) => handleSearchChange(e.target.value)}
            className="block w-full pl-11 pr-10 py-3 border border-gray-200 rounded-xl bg-white shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-amber-500 text-sm transition-all"
            placeholder="Search your content history..."
            aria-label="Search history"
          />
          <AnimatePresence>
            {filters.search && (
              <motion.button
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                type="button"
                onClick={clearSearch}
                className="absolute inset-y-0 right-0 pr-4 flex items-center text-gray-400 hover:text-gray-600 transition-colors"
                aria-label="Clear search"
              >
                <XMarkIcon className="h-5 w-5" aria-hidden="true" />
              </motion.button>
            )}
          </AnimatePresence>
        </div>

        {/* Quick Filter Buttons */}
        <div className="flex items-center gap-2">
          {/* Favorites Toggle */}
          <button
            type="button"
            onClick={handleFavoritesToggle}
            className={`inline-flex items-center gap-2 px-4 py-3 rounded-xl text-sm font-medium transition-all focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 ${
              filters.favorites_only
                ? 'bg-amber-100 text-amber-700 border border-amber-200'
                : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
            }`}
            aria-pressed={filters.favorites_only}
          >
            <StarIcon
              className={`w-5 h-5 ${
                filters.favorites_only ? 'fill-amber-500 text-amber-500' : ''
              }`}
              aria-hidden="true"
            />
            <span>Favorites</span>
            {stats?.favorites !== undefined && stats.favorites > 0 && (
              <span
                className={`inline-flex items-center justify-center px-1.5 py-0.5 rounded-full text-xs ${
                  filters.favorites_only
                    ? 'bg-amber-200 text-amber-800'
                    : 'bg-gray-100 text-gray-500'
                }`}
              >
                {stats.favorites}
              </span>
            )}
          </button>

          {/* Clear All Filters */}
          <AnimatePresence>
            {hasActiveFilters && (
              <motion.button
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                type="button"
                onClick={clearAllFilters}
                className="inline-flex items-center gap-1.5 px-3 py-3 rounded-xl text-sm font-medium text-gray-500 hover:text-gray-700 hover:bg-gray-100 transition-all focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2"
                aria-label="Clear all filters"
              >
                <FunnelIcon className="w-4 h-4" aria-hidden="true" />
                <XMarkIcon className="w-3 h-3" aria-hidden="true" />
              </motion.button>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Category Tabs */}
      <div className="w-full overflow-x-auto scrollbar-hide">
        <nav
          className="flex gap-2 pb-2"
          role="tablist"
          aria-label="Filter by category"
        >
          {categories.map((category, index) => {
            const isSelected = selectedCategory === category.id
            const count =
              category.id === 'all'
                ? stats?.total
                : stats?.byCategory[category.id]

            return (
              <button
                key={category.id}
                ref={(el) => {
                  buttonRefs.current[index] = el
                }}
                type="button"
                role="tab"
                aria-selected={isSelected}
                tabIndex={isSelected ? 0 : -1}
                onClick={() => handleCategoryChange(category.id)}
                onKeyDown={(e) => handleKeyDown(e, index)}
                className={`relative flex-shrink-0 px-4 py-2 rounded-lg text-sm font-medium transition-all focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 ${
                  isSelected
                    ? 'bg-amber-600 text-white shadow-sm'
                    : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50 hover:border-gray-300'
                }`}
              >
                <span className="flex items-center gap-2">
                  {category.name}
                  {count !== undefined && count > 0 && (
                    <span
                      className={`inline-flex items-center justify-center px-1.5 py-0.5 rounded-full text-xs ${
                        isSelected
                          ? 'bg-amber-500 text-amber-100'
                          : 'bg-gray-100 text-gray-500'
                      }`}
                    >
                      {count}
                    </span>
                  )}
                </span>
                {isSelected && (
                  <motion.div
                    layoutId="historyFilterIndicator"
                    className="absolute inset-0 bg-amber-600 rounded-lg -z-10"
                    transition={{ type: 'spring', bounce: 0.2, duration: 0.4 }}
                  />
                )}
              </button>
            )
          })}
        </nav>
      </div>
    </div>
  )
}
