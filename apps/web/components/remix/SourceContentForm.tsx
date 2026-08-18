'use client'

import React from 'react'

interface SourceContentFormProps {
  sourceTitle: string
  sourceContent: string
  isAnalyzing: boolean
  onTitleChange: (title: string) => void
  onContentChange: (content: string) => void
  onAnalyze: () => void
}

function SourceContentFormComponent({
  sourceTitle,
  sourceContent,
  isAnalyzing,
  onTitleChange,
  onContentChange,
  onAnalyze,
}: SourceContentFormProps) {
  const wordCount = sourceContent.split(/\s+/).filter(Boolean).length

  return (
    <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm p-6">
      <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Source Content</h2>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Title
          </label>
          <input
            type="text"
            value={sourceTitle}
            onChange={(e) => onTitleChange(e.target.value)}
            placeholder="Enter your content title..."
            className="w-full px-4 py-2 border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Content Body
          </label>
          <textarea
            value={sourceContent}
            onChange={(e) => onContentChange(e.target.value)}
            placeholder="Paste your blog post, article, or any content here..."
            rows={12}
            className="w-full px-4 py-2 border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-transparent resize-none"
          />
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{wordCount} words</p>
        </div>

        <button
          onClick={onAnalyze}
          disabled={isAnalyzing || !sourceContent.trim()}
          className="w-full py-2 px-4 bg-gray-800 dark:bg-gray-700 text-white rounded-lg hover:bg-gray-700 dark:hover:bg-gray-600 disabled:bg-gray-300 dark:disabled:bg-gray-800 disabled:cursor-not-allowed transition-colors"
        >
          {isAnalyzing ? 'Analyzing...' : 'Analyze Content'}
        </button>
      </div>
    </div>
  )
}

export const SourceContentForm = React.memo(SourceContentFormComponent)
