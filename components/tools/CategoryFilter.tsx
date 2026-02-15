'use client'

import { useRef, useCallback, useMemo } from 'react'
import { motion } from 'framer-motion'
import { ToolCategory, TOOL_CATEGORIES } from '../../types/tools'

interface CategoryFilterProps {
  selectedCategory: ToolCategory | 'all'
  onCategoryChange: (category: ToolCategory | 'all') => void
  toolCounts?: Record<ToolCategory | 'all', number>
}

export default function CategoryFilter({
  selectedCategory,
  onCategoryChange,
  toolCounts,
}: CategoryFilterProps) {
  const categories: Array<{ id: ToolCategory | 'all'; name: string }> = useMemo(
    () => [
      { id: 'all', name: 'All Tools' },
      ...Object.values(TOOL_CATEGORIES).map((cat) => ({
        id: cat.id,
        name: cat.name,
      })),
    ],
    []
  )

  // Refs for keyboard navigation
  const buttonRefs = useRef<(HTMLButtonElement | null)[]>([])

  // Handle keyboard navigation for tabs (arrow keys)
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
          onCategoryChange(nextCategory.id)
        }
      }
    },
    [categories, onCategoryChange]
  )

  return (
    <div className="w-full overflow-x-auto scrollbar-hide">
      <nav
        className="flex gap-2 pb-2"
        role="tablist"
        aria-label="Tool categories"
      >
        {categories.map((category, index) => {
          const isSelected = selectedCategory === category.id
          const count = toolCounts?.[category.id]

          return (
            <button
              key={category.id}
              ref={(el) => { buttonRefs.current[index] = el }}
              type="button"
              role="tab"
              aria-selected={isSelected}
              tabIndex={isSelected ? 0 : -1}
              onClick={() => onCategoryChange(category.id)}
              onKeyDown={(e) => handleKeyDown(e, index)}
              className={`relative flex-shrink-0 px-4 py-2 rounded-lg text-sm font-medium transition-all focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 ${
                isSelected
                  ? 'bg-amber-600 text-white shadow-sm'
                  : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50 hover:border-gray-300'
              }`}
            >
              <span className="flex items-center gap-2">
                {category.name}
                {count !== undefined && (
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
                  layoutId="categoryIndicator"
                  className="absolute inset-0 bg-amber-600 rounded-lg -z-10"
                  transition={{ type: 'spring', bounce: 0.2, duration: 0.4 }}
                />
              )}
            </button>
          )
        })}
      </nav>
    </div>
  )
}
