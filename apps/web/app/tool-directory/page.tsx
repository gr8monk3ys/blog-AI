import Link from 'next/link'
import SiteHeader from '../../components/SiteHeader'
import SiteFooter from '../../components/SiteFooter'
import { buttonVariants } from '../../components/ui/Button'
import {
  TOOL_CATEGORIES,
  SAMPLE_TOOLS,
  type Tool,
  type ToolCategory,
} from '../../types/tools'
import { toolsApi, toFrontendTools } from '../../lib/tools-api'

export const metadata = {
  title: 'Tool Directory',
  description:
    'Browse the complete directory of AI writing tools and templates to build scalable content.',
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

const groupToolsByCategory = (tools: Tool[]) => {
  const grouped: Record<ToolCategory, Tool[]> = CATEGORY_ORDER.reduce(
    (acc, category) => {
      acc[category] = []
      return acc
    },
    {} as Record<ToolCategory, Tool[]>
  )

  tools.forEach((tool) => {
    grouped[tool.category]?.push(tool)
  })

  CATEGORY_ORDER.forEach((category) => {
    grouped[category] = grouped[category].sort((a, b) =>
      a.name.localeCompare(b.name)
    )
  })

  return grouped
}

// The directory on the notebook: a wide index header with the figures as a
// row of wall labels, the categories as a row of wall-label jump links, then
// one hairline-divided ledger per category — the category's name and line on
// the left, its tools as rows on the right (DESIGN.md → Layout: asymmetric
// editorial splits, never equal halves).
export default async function ToolDirectoryPage() {
  const tools = await loadTools()
  const groupedTools = groupToolsByCategory(tools)
  const totalTools = tools.length

  const figures = [
    { value: `${totalTools}+`, label: 'Tools in the directory' },
    { value: String(CATEGORY_ORDER.length), label: 'Categories covered' },
    { value: '2026', label: 'Updated for this year' },
  ]

  return (
    <>
      <SiteHeader />
      <main id="main-content" tabIndex={-1} className="min-h-screen">
        <header className="mx-auto max-w-7xl px-4 pb-10 pt-12 sm:px-6 md:pt-16 lg:px-8">
          <p className="label-mono">Tool Directory</p>
          <h1 className="text-page-title mt-3 max-w-3xl">Browse Every AI Tool in One Place</h1>
          <p className="mt-4 max-w-2xl text-lg leading-relaxed text-muted-foreground text-pretty">
            This directory is designed for discovery and internal linking. Use it to find tools
            by category, jump to a specific section, or explore new ideas for content scale.
          </p>
          <div className="mt-8 flex flex-wrap items-center gap-5">
            <Link href="/tools" className={buttonVariants({ size: 'lg' })}>
              Open Interactive Tools
            </Link>
            <Link href="/" className={labelLink}>
              Back to Home
            </Link>
          </div>

          <ul className="label-mono mt-12 flex flex-wrap gap-x-6 gap-y-2 border-t border-border/60 pt-6">
            {figures.map((figure) => (
              <li key={figure.label}>
                <span className="text-foreground">{figure.value}</span> {figure.label}
              </li>
            ))}
          </ul>
        </header>

        <section className="mx-auto max-w-7xl px-4 pb-4 sm:px-6 lg:px-8">
          <nav
            className="flex flex-wrap items-baseline gap-x-6 gap-y-1 border-y border-border/60 py-5"
            aria-label="Jump to category"
          >
            <span className="label-mono">Jump to category</span>
            {CATEGORY_ORDER.map((category) => (
              <a key={category} href={`#${category}`} className={labelLink}>
                {TOOL_CATEGORIES[category].name}
              </a>
            ))}
          </nav>
        </section>

        <section className="mx-auto max-w-7xl px-4 pb-16 sm:px-6 lg:px-8">
          {CATEGORY_ORDER.map((category) => {
            const categoryInfo = TOOL_CATEGORIES[category]
            const categoryTools = groupedTools[category]
            return (
              <section
                key={category}
                id={category}
                className="grid gap-6 border-b border-border py-10 md:grid-cols-[16rem_1fr] md:gap-12 md:py-12"
                aria-labelledby={`${category}-heading`}
              >
                <div>
                  <p className="label-mono">
                    {categoryInfo.name} · {categoryTools.length}
                  </p>
                  <h2 id={`${category}-heading`} className="text-card-title mt-2">
                    {categoryInfo.description}
                  </h2>
                  <p className="mt-4">
                    <Link href={`/tools/category/${category}`} className={labelLink}>
                      View Tools →
                    </Link>
                  </p>
                </div>

                {categoryTools.length === 0 ? (
                  <p className="text-sm text-muted-foreground">
                    No tools available yet. New tools will appear here as the library expands.
                  </p>
                ) : (
                  <ul className="divide-y divide-border/70 border-y border-border/70">
                    {categoryTools.map((tool) => (
                      <li key={tool.id}>
                        <Link
                          href={`/tools/${tool.slug}`}
                          className="group flex items-start justify-between gap-6 py-4"
                        >
                          <div className="min-w-0">
                            <h3 className="font-medium text-foreground transition-colors group-hover:text-primary">
                              {tool.name}
                            </h3>
                            <p className="mt-1 text-sm text-muted-foreground">{tool.description}</p>
                          </div>
                          <span
                            className="label-mono shrink-0 pt-1 transition-colors group-hover:text-primary"
                            aria-hidden="true"
                          >
                            Open →
                          </span>
                        </Link>
                      </li>
                    ))}
                  </ul>
                )}
              </section>
            )
          })}
        </section>

        <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6 md:py-20 lg:px-8">
          <div className="max-w-2xl">
            <p className="label-mono">Internal linking</p>
            <h2 className="text-section-title mt-3">Build Internal Links and Topical Authority</h2>
            <p className="mt-4 leading-relaxed text-muted-foreground">
              Use this directory to connect your tool pages and blogs. Each tool can anchor
              supporting articles, FAQs, and templates. This interlinking creates topic clusters
              that help search engines understand your content breadth.
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-5">
              <Link href="/templates" className={buttonVariants({ variant: 'outline' })}>
                Explore Templates
              </Link>
              <Link href="/" className={labelLink}>
                Start Generating Content
              </Link>
            </div>
          </div>
        </section>
      </main>
      <SiteFooter />
    </>
  )
}

async function loadTools(): Promise<Tool[]> {
  try {
    const response = await toolsApi.listTools({
      limit: 500,
      include_premium: true,
      include_beta: true,
    })
    const tools = toFrontendTools(response.tools || [])
    return tools.length > 0 ? tools : SAMPLE_TOOLS
  } catch {
    return SAMPLE_TOOLS
  }
}
