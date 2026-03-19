'use client'

import { useState, useId } from 'react'
import ContentGenerator from '../../components/ContentGenerator'
import ExportMenu from '../../components/ExportMenu'
import SEOScorePanel from '../../components/seo/SEOScorePanel'
import type { ContentGenerationResponse, BlogContent } from '../../types/content'

function blogContentToPlainText(content: BlogContent): string {
  const lines: string[] = [content.title, '', content.description, '']
  for (const section of content.sections) {
    lines.push(`## ${section.title}`, '')
    for (const subtopic of section.subtopics) {
      if (subtopic.title) {
        lines.push(`### ${subtopic.title}`, '')
      }
      lines.push(subtopic.content, '')
    }
  }
  return lines.join('\n').trim()
}

export default function GeneratePageClient() {
  const conversationId = useId()
  const [content, setContent] = useState<ContentGenerationResponse | null>(null)
  const [loading, setLoading] = useState(false)

  const blogContent =
    content && content.success && content.type === 'blog' ? content.content : null

  return (
    <div className="min-h-screen">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Generator form */}
        <div className="glass-card rounded-2xl p-8 mb-8">
          <ContentGenerator
            conversationId={conversationId}
            setContent={setContent}
            setLoading={setLoading}
          />
        </div>

        {/* Loading state */}
        {loading && (
          <div className="glass-panel rounded-2xl p-12 flex flex-col items-center justify-center gap-4">
            <svg
              className="animate-spin h-10 w-10 text-amber-600"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            <p className="text-sm text-gray-600 dark:text-gray-400">Generating your blog post…</p>
          </div>
        )}

        {/* Generated content */}
        {!loading && blogContent && (
          <div className="space-y-6">
            {/* Actions bar */}
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                Generated Post
              </h2>
              <ExportMenu
                content={{
                  title: blogContent.title,
                  content: blogContentToPlainText(blogContent),
                  type: 'blog',
                  metadata: {
                    date: blogContent.date,
                    description: blogContent.description,
                    tags: blogContent.tags,
                  },
                }}
              />
            </div>

            {/* Blog article */}
            <article className="glass-card rounded-2xl p-8 space-y-6">
              {/* Header */}
              <header>
                <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-gray-100 font-serif">
                  {blogContent.title}
                </h1>
                {blogContent.description && (
                  <p className="mt-3 text-base text-gray-600 dark:text-gray-400 leading-relaxed">
                    {blogContent.description}
                  </p>
                )}
                {blogContent.tags.length > 0 && (
                  <div className="mt-4 flex flex-wrap gap-2">
                    {blogContent.tags.map((tag) => (
                      <span
                        key={tag}
                        className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-100/80 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </header>

              {/* Sections */}
              <div className="divide-y divide-black/[0.06] dark:divide-white/[0.06]">
                {blogContent.sections.map((section, sectionIdx) => (
                  <section key={sectionIdx} className="pt-6 first:pt-0">
                    <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
                      {section.title}
                    </h2>
                    <div className="space-y-4">
                      {section.subtopics.map((subtopic, subtopicIdx) => (
                        <div key={subtopicIdx}>
                          {subtopic.title && (
                            <h3 className="text-base font-semibold text-gray-800 dark:text-gray-200 mb-2">
                              {subtopic.title}
                            </h3>
                          )}
                          <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
                            {subtopic.content}
                          </p>
                        </div>
                      ))}
                    </div>
                  </section>
                ))}
              </div>
            </article>

            {/* SEO Score Panel (conditional) */}
            {blogContent.seo_score && (
              <SEOScorePanel score={blogContent.seo_score} />
            )}
          </div>
        )}
      </div>
    </div>
  )
}
