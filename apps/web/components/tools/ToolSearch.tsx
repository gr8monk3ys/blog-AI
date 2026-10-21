'use client'

import { MagnifyingGlassIcon, XMarkIcon } from '@heroicons/react/24/outline'
import { inputClassName } from '../ui/Input'

interface ToolSearchProps {
  searchQuery: string
  onSearchChange: (query: string) => void
  placeholder?: string
  resultCount?: number
}

// The field treatment (`input-field`) with the glass in the margin; the
// result count is a wall label announced to assistive tech.
export default function ToolSearch({
  searchQuery,
  onSearchChange,
  placeholder = 'Search tools…',
  resultCount,
}: ToolSearchProps) {
  const handleClear = () => {
    onSearchChange('')
  }

  return (
    <div>
      <div className="relative max-w-xl">
        <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
          <MagnifyingGlassIcon className="size-4 text-muted-foreground" aria-hidden="true" />
        </div>
        <input
          name="searchQuery"
          autoComplete="off"
          type="text"
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          className={`${inputClassName} pl-9 pr-10`}
          placeholder={placeholder}
          aria-label="Search tools"
        />
        {searchQuery && (
          <button
            type="button"
            onClick={handleClear}
            className="absolute inset-y-0 right-0 flex items-center pr-3 text-muted-foreground transition-colors hover:text-primary"
            aria-label="Clear search"
          >
            <XMarkIcon className="size-4" aria-hidden="true" />
          </button>
        )}
      </div>

      {/* Result count, with aria-live for screen reader announcements. */}
      {searchQuery && resultCount !== undefined && (
        <p className="label-mono mt-3" aria-live="polite" aria-atomic="true">
          {resultCount === 0 ? (
            <span>No tools found matching &ldquo;{searchQuery}&rdquo;</span>
          ) : (
            <span>
              Found {resultCount} {resultCount === 1 ? 'tool' : 'tools'} matching
              &ldquo;{searchQuery}&rdquo;
            </span>
          )}
        </p>
      )}
    </div>
  )
}
