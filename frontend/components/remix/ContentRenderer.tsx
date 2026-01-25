'use client'

import React from 'react'
import type { RemixedContent, ContentFormatId } from '@/types/remix'

interface ContentRendererProps {
  result: RemixedContent
}

function ContentRendererComponent({ result }: ContentRendererProps) {
  const content = result.content as Record<string, unknown>

  switch (result.format as ContentFormatId) {
    case 'twitter_thread':
      return (
        <div className="space-y-3">
          <div className="bg-blue-50 p-3 rounded-lg border-l-4 border-blue-400">
            <p className="font-medium text-blue-900">{content.hook as string}</p>
          </div>
          {(content.tweets as string[])?.map((tweet, i) => (
            <div key={i} className="bg-gray-50 p-3 rounded-lg">
              <span className="text-xs text-gray-500">{i + 1}.</span>
              <p className="mt-1">{tweet}</p>
            </div>
          ))}
          <div className="bg-green-50 p-3 rounded-lg border-l-4 border-green-400">
            <p className="font-medium text-green-900">{content.cta as string}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            {(content.hashtags as string[])?.map((tag, i) => (
              <span key={i} className="text-blue-500 text-sm">
                #{tag}
              </span>
            ))}
          </div>
        </div>
      )

    case 'linkedin_post':
      return (
        <div className="space-y-4">
          <p className="font-medium text-lg">{content.hook as string}</p>
          <div className="whitespace-pre-wrap">{content.body as string}</div>
          <p className="font-medium text-blue-600">{content.cta as string}</p>
          <div className="flex flex-wrap gap-2">
            {(content.hashtags as string[])?.map((tag, i) => (
              <span key={i} className="text-blue-500 text-sm">
                #{tag}
              </span>
            ))}
          </div>
        </div>
      )

    case 'email_newsletter':
      return (
        <div className="space-y-4">
          <div className="bg-gray-100 p-3 rounded">
            <p className="text-sm text-gray-500">Subject:</p>
            <p className="font-medium">{content.subject_line as string}</p>
          </div>
          <p className="italic text-gray-600">{content.greeting as string}</p>
          <p>{content.intro as string}</p>
          {(content.sections as { title: string; content: string }[])?.map(
            (section, i) => (
              <div key={i} className="border-l-2 border-gray-200 pl-4">
                <h4 className="font-medium">{section.title}</h4>
                <p className="text-gray-700">{section.content}</p>
              </div>
            )
          )}
          <p className="font-medium text-blue-600">{content.cta as string}</p>
          <p className="text-gray-500">{content.signoff as string}</p>
        </div>
      )

    default:
      return (
        <pre className="whitespace-pre-wrap text-sm bg-gray-50 p-4 rounded-lg overflow-auto">
          {JSON.stringify(content, null, 2)}
        </pre>
      )
  }
}

export const ContentRenderer = React.memo(ContentRendererComponent)
