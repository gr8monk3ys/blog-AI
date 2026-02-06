'use client'

import { useEffect, useMemo, useState } from 'react'
import Link from 'next/link'
import { v4 as uuidv4 } from 'uuid'
import { Tab } from '@headlessui/react'
import {
  SparklesIcon,
  MagnifyingGlassIcon,
  DocumentDuplicateIcon,
  NewspaperIcon,
  BuildingOffice2Icon,
  EnvelopeIcon,
  ChatBubbleLeftRightIcon,
  PlayCircleIcon,
  PencilSquareIcon,
} from '@heroicons/react/24/outline'
import ContentGenerator from '../components/ContentGenerator'
import BookGenerator from '../components/BookGenerator'
import ContentViewer from '../components/ContentViewer'
import SiteHeader from '../components/SiteHeader'
import SiteFooter from '../components/SiteFooter'
import { ContentGenerationResponse } from '../types/content'
import {
  SAMPLE_TOOLS,
  TOOL_CATEGORIES,
  type Tool,
  type ToolCategory,
} from '../types/tools'
import { toolsApi, toFrontendTools } from '../lib/tools-api'

function classNames(...classes: string[]) {
  return classes.filter(Boolean).join(' ')
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

type IconType = React.ComponentType<React.SVGProps<SVGSVGElement>>

const CATEGORY_ICONS: Record<ToolCategory, IconType> = {
  blog: NewspaperIcon,
  seo: MagnifyingGlassIcon,
  email: EnvelopeIcon,
  'social-media': ChatBubbleLeftRightIcon,
  business: BuildingOffice2Icon,
  naming: SparklesIcon,
  video: PlayCircleIcon,
  rewriting: PencilSquareIcon,
}

interface CategoryCard {
  id: ToolCategory | 'templates'
  name: string
  count?: number
  href: string
  icon: IconType
}

const DEFAULT_LATEST_BLOGS = [
  {
    title: 'How AI is changing content strategy for startups',
    date: 'February 1, 2026',
    excerpt:
      'A practical look at how smaller teams use AI to scale research, ideation, and distribution.',
    href: '/history',
  },
  {
    title: 'A field guide to SEO at scale: templates, tools, and workflows',
    date: 'January 27, 2026',
    excerpt:
      'Build repeatable templates that unlock long-tail traffic and reduce editorial overhead.',
    href: '/history',
  },
  {
    title: 'The content ops stack: a lean blueprint for 2026',
    date: 'January 19, 2026',
    excerpt:
      'From briefs to distribution, a lightweight system to keep quality high at volume.',
    href: '/history',
  },
]

const faqs = [
  {
    q: 'How do I generate a blog post?',
    a: 'Pick a topic, add keywords, and choose a tone. The generator will draft a structured post with sections and FAQs.',
  },
  {
    q: 'Can I scale content with templates?',
    a: 'Yes. Templates let you standardize structure so you can publish faster without sacrificing quality.',
  },
  {
    q: 'Do tools help with SEO?',
    a: 'The tool library focuses on metadata, headings, and content planning to support search visibility.',
  },
  {
    q: 'Is this free to use?',
    a: 'A free tier is available, with usage limits. You can upgrade for higher output.',
  },
]

export default function Home() {
  const [conversationId] = useState(uuidv4())
  const [content, setContent] = useState<ContentGenerationResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [tools, setTools] = useState<Tool[]>(SAMPLE_TOOLS)
  const [toolCategories, setToolCategories] = useState<
    Array<{ id: ToolCategory; name: string; count: number }>
  >(() => buildCategoryStatsFromTools(SAMPLE_TOOLS))
  const [latestBlogs, setLatestBlogs] = useState(DEFAULT_LATEST_BLOGS)

  useEffect(() => {
    let isMounted = true

    const loadTools = async () => {
      try {
        const [categoriesResponse, toolsResponse] = await Promise.all([
          toolsApi.listCategories(),
          toolsApi.listTools({ limit: 200, include_premium: true, include_beta: true }),
        ])

        const frontendTools = toFrontendTools(toolsResponse.tools || [])
        if (isMounted && frontendTools.length > 0) {
          setTools(frontendTools)
        }

        const categoriesFromApi = normalizeCategoryStats(categoriesResponse)
        if (isMounted && categoriesFromApi.length > 0) {
          setToolCategories(categoriesFromApi)
        } else if (isMounted && frontendTools.length > 0) {
          setToolCategories(buildCategoryStatsFromTools(frontendTools))
        }
      } catch {
        if (isMounted) {
          setTools(SAMPLE_TOOLS)
          setToolCategories(buildCategoryStatsFromTools(SAMPLE_TOOLS))
        }
      }
    }

    loadTools()

    return () => {
      isMounted = false
    }
  }, [])

  useEffect(() => {
    let isMounted = true

    const loadBlogs = async () => {
      try {
        const response = await fetch('/api/blog?limit=3')
        if (!response.ok) return
        const data = await response.json()
        if (!Array.isArray(data?.data)) return

        const normalized = data.data.map((post: {
          title: string
          date: string
          excerpt: string
          slug: string
        }) => ({
          title: post.title,
          date: formatDisplayDate(post.date),
          excerpt: post.excerpt,
          href: `/blog/${post.slug}`,
        }))

        if (isMounted && normalized.length > 0) {
          setLatestBlogs(normalized)
        }
      } catch {
        // keep fallback
      }
    }

    loadBlogs()

    return () => {
      isMounted = false
    }
  }, [])

  const categoryCards = useMemo<CategoryCard[]>(() => {
    const cards: CategoryCard[] = toolCategories.map((category) => ({
      id: category.id,
      name: category.name,
      count: category.count,
      href: `/tools/category/${category.id}`,
      icon: CATEGORY_ICONS[category.id],
    }))

    cards.push({
      id: 'templates',
      name: 'Templates',
      href: '/templates',
      icon: DocumentDuplicateIcon,
    })

    return cards
  }, [toolCategories])

  const popularTools = useMemo(
    () =>
      [...tools]
        .sort((a, b) => {
          if (a.isPopular && !b.isPopular) return -1
          if (!a.isPopular && b.isPopular) return 1
          if (a.isNew && !b.isNew) return -1
          if (!a.isNew && b.isNew) return 1
          return a.name.localeCompare(b.name)
        })
        .slice(0, 12)
        .map((tool) => ({
          title: tool.name,
          href: `/tools/${tool.slug}`,
        })),
    [tools]
  )

  const toolCount = tools.length
  const categoryCount = toolCategories.length

  return (
    <main className="min-h-screen">
      <SiteHeader />

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-14 sm:py-20">
          <div className="grid grid-cols-1 lg:grid-cols-[1.1fr,0.9fr] gap-10 items-center">
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-100/70 text-amber-800 text-xs font-medium">
                <NewspaperIcon className="w-4 h-4" />
                New: 100+ templates rolling out in 2026
              </div>
              <h1 className="mt-4 text-4xl sm:text-5xl lg:text-6xl font-semibold tracking-tight text-gray-900 font-serif">
                Build a content engine with calculators, blogs, and AI tools.
              </h1>
              <p className="mt-4 text-lg text-gray-600 max-w-xl">
                Create hundreds of targeted pages with structured tools, templates, and automated content.
                Discover popular topics, generate drafts, and publish faster.
              </p>
              <div className="mt-6">
                <div className="flex flex-col sm:flex-row gap-3">
                  <div className="flex items-center gap-2 w-full sm:max-w-md glass-card rounded-lg px-3 py-2">
                    <MagnifyingGlassIcon className="w-5 h-5 text-amber-500" />
                    <input
                      type="text"
                      placeholder="Search tools, templates, or topics"
                      className="w-full text-sm bg-transparent focus:outline-none"
                    />
                  </div>
                  <Link
                    href="/tools"
                    className="inline-flex items-center justify-center px-5 py-2.5 text-sm font-medium text-white bg-amber-600 hover:bg-amber-700 rounded-lg transition-colors"
                  >
                    Explore Library
                  </Link>
                </div>
                <div className="mt-4 flex flex-wrap gap-2 text-xs text-gray-600">
                  <span className="uppercase tracking-wide text-gray-400">Trending</span>
                  {['SEO', 'Marketing', 'Fitness', 'Finance', 'Travel', 'Ecommerce'].map((tag) => (
                    <Link
                      key={tag}
                      href="/tools"
                      className="px-2.5 py-1 rounded-full bg-amber-50/80 hover:bg-amber-100 hover:text-amber-800 transition-colors"
                    >
                      {tag}
                    </Link>
                  ))}
                </div>
              </div>
                <div className="mt-8 grid grid-cols-3 gap-4 max-w-lg">
                  <div>
                  <div className="text-2xl font-semibold text-gray-900">
                    {toolCount > 0 ? `${toolCount}+` : '300+'}
                  </div>
                  <div className="text-xs text-gray-500">Tool pages</div>
                  </div>
                  <div>
                  <div className="text-2xl font-semibold text-gray-900">8k+</div>
                  <div className="text-xs text-gray-500">Articles generated</div>
                  </div>
                  <div>
                  <div className="text-2xl font-semibold text-gray-900">
                    {categoryCount > 0 ? `${categoryCount}+` : '8+'}
                  </div>
                  <div className="text-xs text-gray-500">Categories</div>
                  </div>
                </div>
            </div>

            <div className="glass-card rounded-2xl p-6">
              <div className="flex items-center gap-2 mb-4">
                <SparklesIcon className="w-5 h-5 text-amber-600" />
                <p className="text-sm font-semibold text-gray-900">Quick Generator</p>
              </div>
              <p className="text-sm text-gray-600 mb-4">
                Generate a blog post or book draft in minutes. Use this to seed your content pipeline.
              </p>
              <div className="flex flex-col gap-2">
                <Link
                  href="#generator"
                  className="inline-flex items-center justify-center px-4 py-2 text-sm font-medium text-white bg-amber-600 hover:bg-amber-700 rounded-lg transition-colors"
                >
                  Open Generator
                </Link>
                <Link
                  href="/tools"
                  className="inline-flex items-center justify-center px-4 py-2 text-sm font-medium text-amber-800 bg-amber-50/70 border border-amber-100 hover:bg-amber-100 rounded-lg transition-colors"
                >
                  Browse all tools
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Categories */}
      <section className="bg-white/70 border-y border-amber-100/60 backdrop-blur">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 sm:py-14">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-semibold text-gray-900 font-serif">Browse Categories</h2>
            <Link href="/tools" className="text-sm text-amber-600 hover:text-amber-700">View all tools</Link>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
            {categoryCards.map((category) => (
              <Link
                key={category.name}
                href={category.href}
                className="group glass-card rounded-xl p-4 transition-all hover:shadow-lg"
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-amber-100/70 text-amber-700">
                    <category.icon className="w-5 h-5" />
                  </div>
                  <div className="text-sm font-medium text-gray-900 group-hover:text-amber-800">
                    {category.name}
                  </div>
                  {category.count !== undefined && (
                    <div className="ml-auto text-xs text-amber-700">
                      {category.count}
                    </div>
                  )}
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Popular Tools */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 lg:grid-cols-[1fr,1.1fr] gap-10">
          <div>
            <h2 className="text-2xl font-semibold text-gray-900 font-serif">Most Popular Tools</h2>
            <p className="mt-2 text-sm text-gray-600 max-w-md">
              These are the highest-traffic generators across SEO, marketing, and growth.
            </p>
            <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 gap-3">
              {popularTools.map((tool) => (
                <Link
                  key={tool.title}
                  href={tool.href}
                  className="flex items-center justify-between px-4 py-3 glass-card rounded-lg hover:shadow-md transition-all"
                >
                  <span className="text-sm text-gray-900">{tool.title}</span>
                  <span className="text-xs text-amber-700">Open</span>
                </Link>
              ))}
            </div>
          </div>
          <div className="glass-card rounded-2xl p-6">
            <div className="flex items-center gap-2 mb-4">
              <NewspaperIcon className="w-5 h-5 text-amber-600" />
              <h3 className="text-lg font-semibold text-gray-900">Latest from the Blog</h3>
            </div>
            <div className="space-y-4">
              {latestBlogs.map((post) => (
                <Link key={post.title} href={post.href} className="block group">
                  <div className="text-xs text-gray-500">{post.date}</div>
                  <div className="text-sm font-medium text-gray-900 group-hover:text-amber-800">
                    {post.title}
                  </div>
                  <div className="text-xs text-gray-600 mt-1">{post.excerpt}</div>
                </Link>
              ))}
            </div>
            <div className="mt-6">
              <Link href="/blog" className="text-sm text-amber-700 hover:text-amber-800">
                View all posts
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Generator */}
      <section id="generator" className="bg-gradient-to-b from-white/90 to-amber-50/40 border-y border-amber-100/60">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-semibold text-gray-900 font-serif">Generate Content Fast</h2>
            <p className="mt-2 text-sm text-gray-600">
              Use structured prompts and templates to produce consistent, SEO-ready drafts.
            </p>
          </div>
          <div className="glass-card rounded-2xl p-6">
            <Tab.Group>
              <Tab.List className="flex space-x-1 rounded-xl bg-amber-100/60 p-1 mb-6">
                <Tab
                  className={({ selected }) =>
                    classNames(
                      'w-full rounded-lg py-3 text-sm font-medium leading-5 transition-all',
                      'ring-white ring-opacity-60 ring-offset-2 ring-offset-amber-300 focus:outline-none focus:ring-2',
                      selected
                        ? 'bg-white shadow-sm text-amber-800'
                        : 'text-amber-700 hover:bg-white/[0.12] hover:text-amber-800'
                    )
                  }
                >
                  Blog Post
                </Tab>
                <Tab
                  className={({ selected }) =>
                    classNames(
                      'w-full rounded-lg py-3 text-sm font-medium leading-5 transition-all',
                      'ring-white ring-opacity-60 ring-offset-2 ring-offset-amber-300 focus:outline-none focus:ring-2',
                      selected
                        ? 'bg-white shadow-sm text-amber-800'
                        : 'text-amber-700 hover:bg-white/[0.12] hover:text-amber-800'
                    )
                  }
                >
                  Book
                </Tab>
              </Tab.List>
              <Tab.Panels>
                <Tab.Panel>
                  <ContentGenerator
                    conversationId={conversationId}
                    setContent={setContent}
                    setLoading={setLoading}
                  />
                </Tab.Panel>
                <Tab.Panel>
                  <BookGenerator
                    conversationId={conversationId}
                    setContent={setContent}
                    setLoading={setLoading}
                  />
                </Tab.Panel>
              </Tab.Panels>
            </Tab.Group>
          </div>

          {loading && (
            <div className="mt-8 text-center glass-card rounded-xl p-10">
              <div className="flex justify-center items-center space-x-2">
                <div className="h-3 w-3 bg-amber-300 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                <div className="h-3 w-3 bg-amber-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                <div className="h-3 w-3 bg-amber-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
              </div>
              <p className="mt-6 text-gray-600 font-medium">Generating your content...</p>
              <p className="text-xs text-gray-500 mt-2">This may take a few moments</p>
            </div>
          )}

          {content && !loading && (
            <div className="glass-card rounded-xl p-6 mt-8">
              <ContentViewer content={content} />
            </div>
          )}
        </div>
      </section>

      {/* SEO + FAQ */}
      <section className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 lg:grid-cols-[1.1fr,0.9fr] gap-10">
          <div>
            <h2 className="text-2xl font-semibold text-gray-900 font-serif">Build a Scalable Content Library</h2>
            <p className="mt-3 text-sm text-gray-600">
              Blog AI helps you create a repeatable content system. Start with a calculator or tool page,
              generate supporting blogs, and connect them with internal links. This approach unlocks long-tail
              traffic and builds topical authority over time.
            </p>
            <p className="mt-3 text-sm text-gray-600">
              Use templates to standardize structure, keep quality consistent, and publish at scale. The more
              pages you publish around a topic, the more search visibility you earn.
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <Link href="/tools" className="px-4 py-2 text-sm font-medium text-white bg-amber-600 hover:bg-amber-700 rounded-lg">
                Explore all tools
              </Link>
              <Link href="/templates" className="px-4 py-2 text-sm font-medium text-amber-800 bg-amber-50/70 border border-amber-100 hover:bg-amber-100 rounded-lg">
                View templates
              </Link>
            </div>
          </div>
          <div className="glass-card rounded-2xl p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">FAQs</h3>
            <div className="space-y-4">
              {faqs.map((faq) => (
                <div key={faq.q}>
                  <div className="text-sm font-medium text-gray-900">{faq.q}</div>
                  <div className="text-sm text-gray-600 mt-1">{faq.a}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <SiteFooter />
    </main>
  )
}

function formatDisplayDate(dateValue: string): string {
  const parsed = new Date(dateValue)
  if (Number.isNaN(parsed.getTime())) return dateValue
  return parsed.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

function buildCategoryStatsFromTools(tools: Tool[]): Array<{
  id: ToolCategory
  name: string
  count: number
}> {
  const counts: Record<ToolCategory, number> = CATEGORY_ORDER.reduce(
    (acc, category) => {
      acc[category] = 0
      return acc
    },
    {} as Record<ToolCategory, number>
  )

  tools.forEach((tool) => {
    counts[tool.category] = (counts[tool.category] || 0) + 1
  })

  return CATEGORY_ORDER.map((category) => ({
    id: category,
    name: TOOL_CATEGORIES[category].name,
    count: counts[category] || 0,
  }))
}

function normalizeCategoryStats(
  categories: Array<{ id: string; tool_count?: number }>
): Array<{ id: ToolCategory; name: string; count: number }> {
  if (!Array.isArray(categories)) return []

  const categoryMap = new Map<ToolCategory, number>()

  categories.forEach((category) => {
    if (category.id in TOOL_CATEGORIES) {
      const id = category.id as ToolCategory
      categoryMap.set(id, category.tool_count ?? 0)
    }
  })

  if (categoryMap.size === 0) return []

  return CATEGORY_ORDER.map((category) => ({
    id: category,
    name: TOOL_CATEGORIES[category].name,
    count: categoryMap.get(category) ?? 0,
  }))
}
