'use client'

import { useState, useId } from 'react'
import ContentGenerator from '../../../components/ContentGenerator'
import ExportMenu from '../../../components/ExportMenu'
import SEOScorePanel from '../../../components/seo/SEOScorePanel'
import FactCheckResults from '../../../components/content-generator/FactCheckResults'
import PageHeader from '../../../components/app/PageHeader'
import type { ContentGenerationResponse, BlogContent } from '../../../types/content'

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
    <div className="mx-auto max-w-4xl">
      <PageHeader
        kicker="Write"
        title="Generate Content"
        description="Generate brand-consistent blog posts with AI-powered research, fact-checking, and SEO optimization."
      />

      {/* Generator form: on the page itself, no card. */}
      <ContentGenerator
        conversationId={conversationId}
        setContent={setContent}
        setLoading={setLoading}
      />

      {/* Loading state */}
      {loading && (
        <div
          className="mt-10 flex flex-col items-center justify-center gap-4 border-t border-border py-16"
          role="status"
        >
          <svg
            className="h-8 w-8 animate-spin text-primary"
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
          <p className="label-mono">Generating your blog post…</p>
        </div>
      )}

      {/* Generated content */}
      {!loading && blogContent && (
        <div className="mt-10 space-y-8 border-t border-border pt-8">
          {/* Actions bar */}
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="label-mono">Draft</p>
              <h2 className="text-card-title mt-1">Generated Post</h2>
            </div>
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

          {/* The draft: body sans at the reading measure; the serif speaks only
              in the headings. */}
          <article className="max-w-prose space-y-8">
            <header>
              <h2 className="text-section-title text-foreground">{blogContent.title}</h2>
              {blogContent.description && (
                <p className="mt-3 text-base leading-relaxed text-muted-foreground">
                  {blogContent.description}
                </p>
              )}
              {blogContent.tags.length > 0 && (
                <ul className="mt-4 flex flex-wrap gap-x-4 gap-y-1" aria-label="Tags">
                  {blogContent.tags.map((tag) => (
                    <li key={tag} className="label-mono">
                      {tag}
                    </li>
                  ))}
                </ul>
              )}
            </header>

            <div className="divide-y divide-border">
              {blogContent.sections.map((section, sectionIdx) => (
                <section key={sectionIdx} className="pt-6 first:pt-0 pb-6 last:pb-0">
                  <h3 className="text-card-title mb-4 text-foreground">{section.title}</h3>
                  <div className="space-y-4">
                    {section.subtopics.map((subtopic, subtopicIdx) => (
                      <div key={subtopicIdx}>
                        {subtopic.title && (
                          <h4 className="text-subsection mb-2 text-foreground">{subtopic.title}</h4>
                        )}
                        <p className="text-sm leading-relaxed text-foreground">{subtopic.content}</p>
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

          {/* Fact Check Results (conditional) */}
          {blogContent.fact_check && (
            <FactCheckResults result={blogContent.fact_check} />
          )}
        </div>
      )}
    </div>
  )
}
