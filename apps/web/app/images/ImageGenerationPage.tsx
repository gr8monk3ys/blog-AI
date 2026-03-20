'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { PhotoIcon } from '@heroicons/react/24/outline'
import { API_ENDPOINTS, getDefaultHeaders } from '../../lib/api'
import { useToast } from '../../hooks/useToast'
import SingleImageTab from './components/SingleImageTab'
import BlogImagesTab from './components/BlogImagesTab'
import type { ImageStylesResponse } from '../../types/images'

const TABS = [
  { id: 'single', label: 'Single Image' },
  { id: 'blog', label: 'Blog Images' },
] as const

type TabId = (typeof TABS)[number]['id']

export default function ImageGenerationPage() {
  const [activeTab, setActiveTab] = useState<TabId>('single')
  const [styles, setStyles] = useState<ImageStylesResponse | null>(null)
  const [proAccess, setProAccess] = useState<boolean | null>(null)
  const { showToast, ToastComponent } = useToast()

  useEffect(() => {
    async function checkAccess() {
      try {
        const headers = await getDefaultHeaders()
        const res = await fetch(API_ENDPOINTS.images.health, { headers })
        if (res.status === 402 || res.status === 403) {
          setProAccess(false)
        } else {
          setProAccess(true)
        }
      } catch {
        setProAccess(true)
      }
    }

    async function fetchStyles() {
      try {
        const headers = await getDefaultHeaders()
        const res = await fetch(API_ENDPOINTS.images.styles, { headers })
        if (res.ok) {
          const data: ImageStylesResponse = await res.json()
          setStyles(data)
        }
      } catch {
        // Non-critical
      }
    }

    checkAccess()
    fetchStyles()
  }, [])

  if (proAccess === false) {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-20 text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-amber-100/80 dark:bg-amber-900/40 text-amber-700 mb-6">
          <PhotoIcon className="w-8 h-8" />
        </div>
        <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-3">
          AI Image Generation
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mb-8 max-w-md mx-auto">
          Image generation is available on the Pro plan. Upgrade to generate custom images for your blog posts and social media.
        </p>
        <Link
          href="/pricing"
          className="inline-flex items-center gap-2 px-6 py-3 rounded-lg text-sm font-medium bg-amber-600 text-white hover:bg-amber-700 transition-colors"
        >
          Upgrade to Pro
        </Link>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <div className="flex items-center gap-3 mb-8">
        <div className="inline-flex items-center justify-center w-11 h-11 rounded-xl bg-amber-100/80 dark:bg-amber-900/40 text-amber-700">
          <PhotoIcon className="w-5 h-5" aria-hidden="true" />
        </div>
        <div>
          <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">AI Image Generation</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">Generate images from prompts or blog content</p>
        </div>
      </div>

      {/* Tab bar */}
      <div className="border-b border-gray-200 dark:border-gray-700 mb-6">
        <nav className="flex gap-6" aria-label="Image generation tabs">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              className={`pb-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-amber-600 text-amber-600'
                  : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {activeTab === 'single' && <SingleImageTab styles={styles} showToast={showToast} />}
      {activeTab === 'blog' && <BlogImagesTab styles={styles} showToast={showToast} />}

      <ToastComponent />
    </div>
  )
}
