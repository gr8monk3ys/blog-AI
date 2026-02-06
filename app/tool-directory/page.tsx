import Link from 'next/link'
import SiteHeader from '../../components/SiteHeader'
import SiteFooter from '../../components/SiteFooter'
import {
  TOOL_CATEGORIES,
  SAMPLE_TOOLS,
  type Tool,
  type ToolCategory,
} from '../../types/tools'
import { toolsApi, toFrontendTools } from '../../lib/tools-api'

export const metadata = {
  title: 'Tool Directory | Blog AI',
  description:
    'Browse the complete directory of AI writing tools, calculators, and templates to build scalable content.',
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

export default async function ToolDirectoryPage() {
  const tools = await loadTools()
  const groupedTools = groupToolsByCategory(tools)
  const totalTools = tools.length

  return (
    <main className="min-h-screen bg-gradient-to-b from-neutral-50 via-white to-neutral-100">
      <SiteHeader />

      <header className="border-b border-neutral-200 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-wide text-neutral-500">
                Tool Directory
              </p>
              <h1 className="text-3xl sm:text-4xl font-semibold text-neutral-900 font-serif">
                Browse every AI tool and calculator in one place
              </h1>
              <p className="mt-2 text-sm text-neutral-600 max-w-2xl">
                This directory is designed for discovery and internal linking. Use it
                to find tools by category, jump to a specific section, or explore new
                ideas for content scale.
              </p>
            </div>
            <div className="flex flex-col gap-2">
              <Link
                href="/tools"
                className="inline-flex items-center justify-center px-4 py-2 text-sm font-medium text-white bg-amber-600 hover:bg-amber-700 rounded-lg transition-colors"
              >
                Open Interactive Tools
              </Link>
              <Link
                href="/"
                className="inline-flex items-center justify-center px-4 py-2 text-sm font-medium text-neutral-700 border border-neutral-200 hover:bg-neutral-50 rounded-lg transition-colors"
              >
                Back to Home
              </Link>
            </div>
          </div>
        </div>
      </header>

      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white border border-neutral-200 rounded-xl p-5">
            <div className="text-3xl font-semibold text-neutral-900">
              {totalTools}+
            </div>
            <div className="text-xs text-neutral-500">Tools in the directory</div>
          </div>
          <div className="bg-white border border-neutral-200 rounded-xl p-5">
            <div className="text-3xl font-semibold text-neutral-900">
              {CATEGORY_ORDER.length}
            </div>
            <div className="text-xs text-neutral-500">Categories covered</div>
          </div>
          <div className="bg-white border border-neutral-200 rounded-xl p-5">
            <div className="text-3xl font-semibold text-neutral-900">2026</div>
            <div className="text-xs text-neutral-500">Updated for this year</div>
          </div>
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-10">
        <div className="bg-white border border-neutral-200 rounded-2xl p-6">
          <div className="text-sm font-medium text-neutral-900 mb-4">
            Jump to category
          </div>
          <div className="flex flex-wrap gap-3">
            {CATEGORY_ORDER.map((category) => (
              <a
                key={category}
                href={`#${category}`}
                className="px-3 py-1.5 rounded-full bg-neutral-100 text-xs text-neutral-700 hover:bg-amber-50 hover:text-amber-700 transition-colors"
              >
                {TOOL_CATEGORIES[category].name}
              </a>
            ))}
          </div>
        </div>
      </section>

      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-14">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {CATEGORY_ORDER.map((category) => {
              const categoryInfo = TOOL_CATEGORIES[category]
              const tools = groupedTools[category]
            return (
              <div
                key={category}
                id={category}
                className="bg-white border border-neutral-200 rounded-2xl p-6"
              >
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <div className={`text-xs font-medium ${categoryInfo.color}`}>
                      {categoryInfo.name}
                    </div>
                    <h2 className="text-lg font-semibold text-neutral-900">
                      {categoryInfo.description}
                    </h2>
                  </div>
                  <Link
                    href={`/tools/category/${category}`}
                    className="text-xs text-amber-600 hover:text-amber-700"
                  >
                    View tools
                  </Link>
                </div>

                {tools.length === 0 ? (
                  <div className="text-sm text-neutral-500">
                    No tools available yet. New tools will appear here as the
                    library expands.
                  </div>
                ) : (
                  <ul className="space-y-2">
                    {tools.map((tool) => (
                      <li key={tool.id}>
                        <Link
                          href={`/tools/${tool.slug}`}
                          className="flex items-start justify-between gap-3 rounded-lg px-3 py-2 hover:bg-neutral-50"
                        >
                          <div>
                            <div className="text-sm font-medium text-neutral-900">
                              {tool.name}
                            </div>
                            <div className="text-xs text-neutral-500">
                              {tool.description}
                            </div>
                          </div>
                          <span className="text-xs text-amber-600">Open</span>
                        </Link>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )
          })}
        </div>
      </section>

      <section className="border-t border-neutral-200 bg-white">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <h2 className="text-2xl font-semibold text-neutral-900 font-serif">
            Build internal links and topical authority
          </h2>
          <p className="mt-3 text-sm text-neutral-600">
            Use this directory to connect your calculator pages and blogs. Each tool
            can anchor supporting articles, FAQs, and templates. This interlinking
            creates topic clusters that help search engines understand your content
            breadth.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link
              href="/templates"
              className="px-4 py-2 text-sm font-medium text-white bg-amber-600 hover:bg-amber-700 rounded-lg"
            >
              Explore templates
            </Link>
            <Link
              href="/"
              className="px-4 py-2 text-sm font-medium text-neutral-700 border border-neutral-200 hover:bg-neutral-50 rounded-lg"
            >
              Start generating content
            </Link>
          </div>
        </div>
      </section>

      <SiteFooter />
    </main>
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
