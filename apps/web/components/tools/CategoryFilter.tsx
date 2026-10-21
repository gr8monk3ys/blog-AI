'use client'

import { useRef, useCallback, useMemo } from 'react'
import { ToolCategory, TOOL_CATEGORIES } from '../../types/tools'

interface CategoryFilterProps {
  selectedCategory: ToolCategory | 'all'
  onCategoryChange: (category: ToolCategory | 'all') => void
  toolCounts?: Record<ToolCategory | 'all', number>
}

// The category filter as a row of wall-label tabs (DESIGN.md → Chips: tag
// lists are not chips). The selected tab is in the ink with its underline
// scored in; the count sits beside the name in tabular figures.
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
    <div className="flex flex-wrap items-baseline gap-x-5 gap-y-1" role="tablist" aria-label="Tool categories">
      <span className="label-mono">Filter</span>
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
            className={`label-mono label-link ink-underline gap-1.5 transition-colors hover:text-primary ${
              isSelected ? 'text-primary' : ''
            }`}
          >
            {category.name}
            {count !== undefined && <span className="tabular-nums">({count})</span>}
          </button>
        )
      })}
    </div>
  )
}
