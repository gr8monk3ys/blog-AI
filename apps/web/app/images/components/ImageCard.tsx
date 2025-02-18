'use client'

import { useState } from 'react'
import { ArrowDownTrayIcon, ChevronDownIcon, ChevronUpIcon } from '@heroicons/react/24/outline'
import type { ImageResult } from '../../../types/images'

interface ImageCardProps {
  image: ImageResult
  label?: string
}

export default function ImageCard({ image, label }: ImageCardProps) {
  const [showPrompt, setShowPrompt] = useState(false)

  return (
    <div className="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 overflow-hidden">
      {label && (
        <div className="px-4 py-2 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
          <span className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">{label}</span>
        </div>
      )}

      {/* Image preview */}
      <div className="relative aspect-square bg-gray-100 dark:bg-gray-900">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={image.url}
          alt={image.prompt_used}
          className="w-full h-full object-contain"
        />
      </div>

      <div className="p-4 space-y-3">
        {/* Meta row */}
        <div className="flex flex-wrap gap-2 text-xs">
          <span className="px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 font-medium">
            {image.size}
          </span>
          <span className="px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 font-medium capitalize">
            {image.style}
          </span>
          <span className="px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 font-medium uppercase">
            {image.quality}
          </span>
          <span className="px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 font-medium capitalize">
            {image.provider === 'openai' ? 'DALL-E 3' : 'Stability AI'}
          </span>
        </div>

        {/* Revised prompt (DALL-E 3) */}
        {image.revised_prompt && (
          <p className="text-xs text-gray-500 dark:text-gray-400 italic">
            Revised: {image.revised_prompt}
          </p>
        )}

        {/* Prompt used expandable */}
        <button
          type="button"
          onClick={() => setShowPrompt(!showPrompt)}
          className="flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
        >
          {showPrompt ? <ChevronUpIcon className="w-3 h-3" /> : <ChevronDownIcon className="w-3 h-3" />}
          Prompt used
        </button>
        {showPrompt && (
          <p className="text-xs text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-900 rounded-lg p-3 leading-relaxed">
            {image.prompt_used}
          </p>
        )}

        {/* Download */}
        <a
          href={image.url}
          download
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
        >
          <ArrowDownTrayIcon className="w-3.5 h-3.5" />
          Download
        </a>
      </div>
    </div>
  )
}
