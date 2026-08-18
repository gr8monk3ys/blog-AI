import Link from 'next/link'
import SiteHeader from '../../../../components/SiteHeader'
import SiteFooter from '../../../../components/SiteFooter'
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
      <main className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-950 dark:to-gray-900">

      <header className="border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Link href="/tool-directory" className="text-xs text-gray-500 dark:text-gray-400 hover:text-amber-700 dark:hover:text-amber-300">
            Back to directory
          </Link>
          <h1 className="mt-3 text-3xl sm:text-4xl font-semibold text-gray-900 dark:text-gray-100 font-serif">
            {categoryInfo.name} Tools
          </h1>
          <p className="mt-2 text-sm text-gray-600 dark:text-gray-400 max-w-2xl">
            {categoryInfo.description}. Explore calculators and generators tailored for
            {` ${categoryInfo.name.toLowerCase()} workflows.`}
          </p>
        </div>
      </header>

      <section className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        {tools.length === 0 ? (
          <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-6 text-sm text-gray-600 dark:text-gray-400">
            No tools available yet for this category.
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {tools.map((tool) => (
              <Link
                key={tool.id}
                href={`/tools/${tool.slug}`}
                className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-5 hover:border-amber-200 dark:hover:border-amber-800 hover:shadow-sm transition-all"
              >
                <div className="text-sm font-medium text-gray-900 dark:text-gray-100">{tool.name}</div>
                <div className="mt-2 text-xs text-gray-600 dark:text-gray-400">{tool.description}</div>
                <div className="mt-3 text-xs text-amber-600 dark:text-amber-400">Open tool</div>
              </Link>
            ))}
          </div>
        )}
      </section>

      <section className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 pb-12">
        <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            Why {categoryInfo.name.toLowerCase()} tools matter
          </h2>
          <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
            {categoryInfo.name} workflows benefit from consistent structure and fast iteration.
            Use these tools to generate drafts, improve quality, and maintain momentum across your
            content pipeline.
          </p>
          <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
            Pair each tool with supporting articles and templates to build topic clusters that
            increase search visibility.
          </p>
        </div>
      </section>

      <section className="border-t border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 font-serif">
            Related categories
          </h2>
          <div className="mt-4 flex flex-wrap gap-3">
            {CATEGORY_ORDER.filter((id) => id !== categoryId).map((id) => (
              <Link
                key={id}
                href={`/tools/category/${id}`}
                className="px-3 py-1.5 rounded-full bg-gray-100 dark:bg-gray-800 text-xs text-gray-700 dark:text-gray-300 hover:bg-amber-50 dark:hover:bg-amber-900/30 hover:text-amber-700 dark:hover:text-amber-300 transition-colors"
              >
                {TOOL_CATEGORIES[id].name}
              </Link>
            ))}
          </div>
        </div>
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
