'use client'

import { useMemo } from 'react'
import ToolCard, { type HeadingLevel } from './ToolCard'
import ToolSearch from './ToolSearch'
import CategoryFilter from './CategoryFilter'
import { buttonVariants } from '../ui/Button'
import { Tool, ToolCategory, SAMPLE_TOOLS } from '../../types/tools'
import { useUrlSearchParam } from '../../hooks/useUrlSearchParam'
import { TOOL_CATEGORIES } from '../../types/tools'

interface ToolGridProps {
  tools?: Tool[]
  showFilters?: boolean
  showSearch?: boolean
  initialCategory?: ToolCategory | 'all'
  /**
   * Heading level for the tool row titles and the empty state. Defaults to 3,
   * which is correct when the list sits under a section <h2>. Pass 2 when the
   * list is the first content under the page <h1>.
   */
  headingLevel?: HeadingLevel
}

const isToolCategoryParam = (value: string): value is ToolCategory | 'all' =>
  value === 'all' || value in TOOL_CATEGORIES

// The catalogue: search and filters as wall labels, then the tools as
// hairline rows in two columns at md (DESIGN.md → Components → Cards / Rows).
// Filters live in the URL (?q=&category=&free=1) so a filtered view can be
// shared and survives Back/Forward. Nothing animates in or out.
export default function ToolGrid({
  tools = SAMPLE_TOOLS,
  showFilters = true,
  showSearch = true,
  initialCategory = 'all',
  headingLevel = 3,
}: ToolGridProps) {
  const EmptyStateHeading = `h${headingLevel}` as const
  const [searchQuery, setSearchQuery] = useUrlSearchParam<string>('q', '')
  const [selectedCategory, setSelectedCategory] = useUrlSearchParam<ToolCategory | 'all'>(
    'category',
    initialCategory,
    isToolCategoryParam
  )
  const [freeParam, setFreeParam] = useUrlSearchParam<'' | '1'>('free', '')
  const showFreeOnly = freeParam === '1'
  const setShowFreeOnly = (next: boolean) => setFreeParam(next ? '1' : '')

  // Filter tools based on search, category, and free filter
  const filteredTools = useMemo(() => {
    let result = tools

    // Filter by category
    if (selectedCategory !== 'all') {
      result = result.filter((tool) => tool.category === selectedCategory)
    }

    // Filter by search query
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase().trim()
      result = result.filter(
        (tool) =>
          tool.name.toLowerCase().includes(query) ||
          tool.description.toLowerCase().includes(query) ||
          tool.category.toLowerCase().includes(query)
      )
    }

    // Filter by free only
    if (showFreeOnly) {
      result = result.filter((tool) => tool.isFree)
    }

    return result
  }, [tools, selectedCategory, searchQuery, showFreeOnly])

  // Calculate tool counts per category
  const toolCounts = useMemo(() => {
    const counts: Record<ToolCategory | 'all', number> = {
      all: tools.length,
      blog: 0,
      email: 0,
      'social-media': 0,
      business: 0,
      naming: 0,
      video: 0,
      seo: 0,
      rewriting: 0,
    }

    tools.forEach((tool) => {
      counts[tool.category]++
    })

    return counts
  }, [tools])

  // Sort tools: popular first, then new, then alphabetically
  const sortedTools = useMemo(() => {
    return [...filteredTools].sort((a, b) => {
      if (a.isPopular && !b.isPopular) return -1
      if (!a.isPopular && b.isPopular) return 1
      if (a.isNew && !b.isNew) return -1
      if (!a.isNew && b.isNew) return 1
      return a.name.localeCompare(b.name)
    })
  }, [filteredTools])

  return (
    <div className="space-y-8">
      {/* Search and filter controls */}
      {(showSearch || showFilters) && (
        <div className="space-y-5">
          {showSearch && (
            <ToolSearch
              searchQuery={searchQuery}
              onSearchChange={setSearchQuery}
              placeholder="Search for tools (e.g. blog, email, SEO)…"
              resultCount={searchQuery ? filteredTools.length : undefined}
            />
          )}

          {showFilters && (
            <div className="flex flex-col gap-3 border-y border-border/60 py-4 sm:flex-row sm:items-baseline sm:justify-between sm:gap-8">
              <CategoryFilter
                selectedCategory={selectedCategory}
                onCategoryChange={setSelectedCategory}
                toolCounts={toolCounts}
              />

              <button
                type="button"
                onClick={() => setShowFreeOnly(!showFreeOnly)}
                className={`label-mono label-link ink-underline shrink-0 transition-colors hover:text-primary ${
                  showFreeOnly ? 'text-primary' : ''
                }`}
                aria-pressed={showFreeOnly}
              >
                Free Only
              </button>
            </div>
          )}
        </div>
      )}

      {/* Results summary */}
      <p className="label-mono">
        Showing {sortedTools.length} of {tools.length} tools
      </p>

      {sortedTools.length > 0 ? (
        <ul className="border-t border-border md:grid md:grid-cols-2 md:gap-x-12">
          {sortedTools.map((tool) => (
            <ToolCard key={tool.id} tool={tool} headingLevel={headingLevel} />
          ))}
        </ul>
      ) : (
        // An honest empty state: a wall label, one serif line, one action.
        <div className="border-y border-border py-10">
          <p className="label-mono">No results</p>
          <EmptyStateHeading className="text-card-title mt-3">No tools found</EmptyStateHeading>
          <p className="mt-2 max-w-md text-sm text-muted-foreground">
            Try adjusting your search or filter criteria to find what you’re looking for.
          </p>
          <button
            type="button"
            onClick={() => {
              setSearchQuery('')
              setSelectedCategory('all')
              setShowFreeOnly(false)
            }}
            className={buttonVariants({ variant: 'outline', className: 'mt-6' })}
          >
            Clear All Filters
          </button>
        </div>
      )}
    </div>
  )
}
