'use client'

import React, { memo } from 'react'
import { PlusIcon } from '@heroicons/react/24/outline'

interface SampleFormProps {
  title: string
  content: string
  contentType: string
  isLoading: boolean
  onTitleChange: (value: string) => void
  onContentChange: (value: string) => void
  onContentTypeChange: (value: string) => void
  onSubmit: () => void
}

function SampleFormComponent({
  title,
  content,
  contentType,
  isLoading,
  onTitleChange,
  onContentChange,
  onContentTypeChange,
  onSubmit,
}: SampleFormProps) {
  const wordCount = content.split(/\s+/).filter(Boolean).length

  return (
    <div className="bg-white rounded-xl shadow-sm p-6">
      <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <PlusIcon className="w-5 h-5" />
        Add Voice Sample
      </h2>

      <div className="space-y-4">
        <input
          type="text"
          value={title}
          onChange={(e) => onTitleChange(e.target.value)}
          placeholder="Sample title (optional)"
          className="w-full px-4 py-2 border border-gray-200 rounded-lg"
        />

        <select
          value={contentType}
          onChange={(e) => onContentTypeChange(e.target.value)}
          className="w-full px-4 py-2 border border-gray-200 rounded-lg"
        >
          <option value="text">General Text</option>
          <option value="blog">Blog Post</option>
          <option value="email">Email</option>
          <option value="social">Social Media</option>
          <option value="website">Website Copy</option>
        </select>

        <textarea
          value={content}
          onChange={(e) => onContentChange(e.target.value)}
          placeholder="Paste your content sample here... (min 50 characters)"
          rows={6}
          className="w-full px-4 py-2 border border-gray-200 rounded-lg resize-none"
        />

        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-500">{wordCount} words</span>
          <button
            onClick={onSubmit}
            disabled={isLoading || content.length < 50}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-300"
          >
            Add Sample
          </button>
        </div>
      </div>
    </div>
  )
}

export const SampleForm = memo(SampleFormComponent)
export default SampleForm
