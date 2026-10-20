'use client'

import { useRef, useCallback, useMemo } from 'react'
import {
  MagnifyingGlassIcon,
  XMarkIcon,
  StarIcon,
  FunnelIcon,
} from '@heroicons/react/24/outline'
import { Input } from '../ui/Input'
import { Button } from '../ui/Button'
import { cn } from '../../lib/cn'
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

/**
 * The history list's controls: a search field, the Favorites toggle (a
 * paper-card button that takes the ink when pressed), and the category
 * filter as a hairline-bottomed row of tabs where the selected tab carries a
 * 2px ink rule. Counts are mono figures.
 */
export default function HistoryFilters({
  filters,
  onFiltersChange,
  stats,
}: HistoryFiltersProps) {
  const searchInputRef = useRef<HTMLInputElement>(null)

  const categories: Array<{ id: ToolCategory | 'all'; name: string }> = useMemo(
    () => [
      { id: 'all', name: 'All' },
      ...Object.values(TOOL_CATEGORIES).map((cat) => ({
        id: cat.id,
        name: cat.name,
      })),
    ],
    []
  )

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
      <div className="flex flex-col gap-3 sm:flex-row">
        {/* Search */}
        <div className="relative flex-1">
          <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
            <MagnifyingGlassIcon className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
          </div>
          <Input
            name="search"
            autoComplete="off"
            ref={searchInputRef}
            type="text"
            value={filters.search || ''}
            onChange={(e) => handleSearchChange(e.target.value)}
            className="pl-9 pr-9"
            placeholder="Search your content history…"
            aria-label="Search history"
          />
          {filters.search && (
            <button
              type="button"
              onClick={clearSearch}
              className="absolute inset-y-0 right-0 flex items-center pr-3 text-muted-foreground transition-colors hover:text-primary"
              aria-label="Clear search"
            >
              <XMarkIcon className="h-4 w-4" aria-hidden="true" />
            </button>
          )}
        </div>

        {/* Quick Filter Buttons */}
        <div className="flex items-center gap-2">
          <Button
            type="button"
            variant="secondary"
            onClick={handleFavoritesToggle}
            className={cn(filters.favorites_only && 'border-primary/45 bg-primary/5 text-primary')}
            aria-pressed={filters.favorites_only}
          >
            <StarIcon className="h-4 w-4" aria-hidden="true" />
            <span>Favorites</span>
            {stats?.favorites !== undefined && stats.favorites > 0 && (
              <span className="font-mono text-xs tabular-nums text-muted-foreground">{stats.favorites}</span>
            )}
          </Button>

          {hasActiveFilters && (
            <Button
              type="button"
              variant="ghost"
              size="icon"
              onClick={clearAllFilters}
              aria-label="Clear all filters"
              className="text-muted-foreground"
            >
              <FunnelIcon className="h-4 w-4" aria-hidden="true" />
              <XMarkIcon className="h-3 w-3" aria-hidden="true" />
            </Button>
          )}
        </div>
      </div>

      {/* Category Tabs */}
      <div className="w-full overflow-x-auto">
        <nav className="flex gap-1 border-b border-border" role="tablist" aria-label="Filter by category">
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
                className={cn(
                  '-mb-px flex shrink-0 items-center gap-2 border-b-2 px-3 py-2 text-sm font-medium transition-colors',
                  isSelected
                    ? 'border-primary text-primary'
                    : 'border-transparent text-muted-foreground hover:text-foreground'
                )}
              >
                {category.name}
                {count !== undefined && count > 0 && (
                  <span className="font-mono text-xs tabular-nums text-muted-foreground">{count}</span>
                )}
              </button>
            )
          })}
        </nav>
      </div>
    </div>
  )
}
