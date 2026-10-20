import Link from 'next/link'
import SiteHeader from '../../../../components/SiteHeader'
import SiteFooter from '../../../../components/SiteFooter'
import ToolCard from '../../../../components/tools/ToolCard'
import { notFound } from 'next/navigation'
import {
  TOOL_CATEGORIES,
  SAMPLE_TOOLS,
  type Tool,
  type ToolCategory,
} from '../../../../types/tools'
import { toolsApi, toFrontendTools } from '../../../../lib/tools-api'

interface CategoryPageProps {
  params: Promise<{ category: string }>
}

const CATEGORY_ORDER: ToolCategory[] = [
  'blog',
  'seo',
  'email',
  'social-media',
  'business',
  'naming',
  'video',
  'rewriting',
]

const labelLink = 'label-mono label-link ink-underline transition-colors hover:text-primary'

export async function generateMetadata({ params }: CategoryPageProps) {
  const { category } = await params
  const categoryId = normalizeCategoryParam(category)
  if (!(categoryId in TOOL_CATEGORIES)) return {}

  const categoryInfo = TOOL_CATEGORIES[categoryId]
  return {
    title: `${categoryInfo.name} Tools | Blog AI`,
    description: `Browse ${categoryInfo.name.toLowerCase()} tools to generate content at scale.`,
  }
}

// A category on the notebook: an index header, the tools as hairline rows,
// a short essay at the reading measure, and the other categories as a row of
// wall-label links (DESIGN.md → Chips: tag lists are not chips).
export default async function ToolCategoryPage({ params }: CategoryPageProps) {
  const { category } = await params
  const categoryId = normalizeCategoryParam(category)

  if (!(categoryId in TOOL_CATEGORIES)) {
    notFound()
  }

  const categoryInfo = TOOL_CATEGORIES[categoryId]
  const tools = await loadTools(categoryId)

  return (
    <>
      <SiteHeader />
      <main id="main-content" tabIndex={-1} className="min-h-screen">
        <header className="mx-auto max-w-5xl px-4 pb-10 pt-12 sm:px-6 md:pt-16 lg:px-8">
          <Link href="/tool-directory" className={labelLink}>
            ← Back to Directory
          </Link>
          <p className="label-mono mt-8">
            {categoryInfo.name} · {tools.length} {tools.length === 1 ? 'tool' : 'tools'}
          </p>
          <h1 className="text-page-title mt-3">{categoryInfo.name} Tools</h1>
          <p className="mt-4 max-w-2xl text-lg leading-relaxed text-muted-foreground text-pretty">
            {categoryInfo.description}. Explore generators tailored for
            {` ${categoryInfo.name.toLowerCase()} workflows.`}
          </p>
        </header>

        <section className="mx-auto max-w-5xl px-4 pb-16 sm:px-6 lg:px-8">
          {tools.length === 0 ? (
            <div className="border-y border-border py-10">
              <p className="label-mono">Nothing here yet</p>
              <h2 className="text-card-title mt-3">No tools available yet for this category.</h2>
              <p className="mt-2 text-sm text-muted-foreground">
                New tools will appear here as the library expands.
              </p>
            </div>
          ) : (
            <ul className="border-t border-border md:grid md:grid-cols-2 md:gap-x-12">
              {tools.map((tool) => (
                <ToolCard key={tool.id} tool={tool} headingLevel={2} />
              ))}
            </ul>
          )}
        </section>

        <hr className="gallery-rule" />

        <section className="mx-auto max-w-5xl px-4 py-16 sm:px-6 md:py-20 lg:px-8">
          <div className="max-w-2xl">
            <p className="label-mono">Why it matters</p>
            <h2 className="text-section-title mt-3">
              Why {categoryInfo.name.toLowerCase()} tools matter
            </h2>
            <p className="mt-4 leading-relaxed text-muted-foreground">
              {categoryInfo.name} workflows benefit from consistent structure and fast iteration.
              Use these tools to generate drafts, improve quality, and maintain momentum across
              your content pipeline.
            </p>
            <p className="mt-4 leading-relaxed text-muted-foreground">
              Pair each tool with supporting articles and templates to build topic clusters that
              increase search visibility.
            </p>
          </div>
        </section>

        <hr className="gallery-rule" />

        <section className="mx-auto max-w-5xl px-4 py-12 sm:px-6 md:py-16 lg:px-8">
          <h2 className="label-mono">Related Categories</h2>
          <nav
            className="mt-4 flex flex-wrap items-baseline gap-x-6 gap-y-1"
            aria-label="Related categories"
          >
            {CATEGORY_ORDER.filter((id) => id !== categoryId).map((id) => (
              <Link key={id} href={`/tools/category/${id}`} className={labelLink}>
                {TOOL_CATEGORIES[id].name}
              </Link>
            ))}
          </nav>
        </section>
      </main>
      <SiteFooter />
    </>
  )
}

function normalizeCategoryParam(category: string): ToolCategory {
  const normalized = decodeURIComponent(category).trim().toLowerCase().replace(/_/g, '-')
  return normalized as ToolCategory
}

async function loadTools(category: ToolCategory): Promise<Tool[]> {
  try {
    const response = await toolsApi.listTools({
      category,
      limit: 500,
      include_premium: true,
      include_beta: true,
    })
    const tools = toFrontendTools(response.tools || [])
    return tools.length > 0 ? tools : SAMPLE_TOOLS.filter((tool) => tool.category === category)
  } catch {
    return SAMPLE_TOOLS.filter((tool) => tool.category === category)
  }
}
