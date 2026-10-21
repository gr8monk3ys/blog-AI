import Link from 'next/link'
import { Tool, TOOL_CATEGORIES } from '../../types/tools'

export type HeadingLevel = 2 | 3 | 4 | 5 | 6

interface ToolCardProps {
  tool: Tool
  /**
   * Heading level for the row title. Defaults to 3, which is correct when the
   * list sits under a section <h2>. Pass 2 when the rows are the first
   * headings under the page <h1>, so the outline stays sequential (WCAG 1.3.1
   * / axe heading-order).
   */
  headingLevel?: HeadingLevel
}

/**
 * One tool as a hairline row (DESIGN.md → Components → Cards / Rows): a wall
 * label with the category and its flags, a Fraunces title that takes the ink
 * on hover, a two-line description in Ink Muted, and "Open" in the margin.
 * Server-safe: no hooks, no motion. Rendered inside a <ul>.
 */
export default function ToolCard({ tool, headingLevel = 3 }: ToolCardProps) {
  const Heading = `h${headingLevel}` as const
  const categoryInfo = TOOL_CATEGORIES[tool.category]
  const flags = [
    categoryInfo.name,
    tool.isNew ? 'New' : null,
    tool.isPopular ? 'Popular' : null,
    tool.isFree ? 'Free' : null,
  ].filter((flag): flag is string => flag !== null)

  return (
    <li className="border-b border-border">
      <Link
        href={`/tools/${tool.slug}`}
        className="group flex items-start justify-between gap-6 py-5"
      >
        <div className="min-w-0">
          <p className="label-mono">{flags.join(' · ')}</p>
          <Heading className="text-card-title mt-1.5 transition-colors group-hover:text-primary">
            {tool.name}
          </Heading>
          <p className="mt-1.5 line-clamp-2 text-sm leading-relaxed text-muted-foreground">
            {tool.description}
          </p>
        </div>
        <span
          className="label-mono shrink-0 pt-1 transition-colors group-hover:text-primary"
          aria-hidden="true"
        >
          Open →
        </span>
      </Link>
    </li>
  )
}
