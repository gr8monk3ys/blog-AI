'use client'

import { useState } from 'react'
import { API_ENDPOINTS, getDefaultHeaders } from '../../../lib/api'
import type { ToastOptions } from '../../../hooks/useToast'
import type { BlogImagesResult, ImageProvider, ImageStyle, ImageQuality, ImageStylesResponse } from '../../../types/images'
import StyleSelector from './StyleSelector'
import ImageCard from './ImageCard'

interface BlogImagesTabProps {
  styles: ImageStylesResponse | null
  showToast: (opts: ToastOptions) => void
}

export default function BlogImagesTab({ styles, showToast }: BlogImagesTabProps) {
  const [content, setContent] = useState('')
  const [title, setTitle] = useState('')
  const [keywords, setKeywords] = useState<string[]>([])
  const [keywordInput, setKeywordInput] = useState('')
  const [generateFeatured, setGenerateFeatured] = useState(true)
  const [generateSocial, setGenerateSocial] = useState(true)
  const [inlineCount, setInlineCount] = useState(0)
  const [provider, setProvider] = useState<ImageProvider>('openai')
  const [style, setStyle] = useState<ImageStyle>('natural')
  const [quality, setQuality] = useState<ImageQuality>('standard')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<BlogImagesResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  function addKeyword() {
    const kw = keywordInput.trim()
    if (kw && !keywords.includes(kw) && keywords.length < 20) {
      setKeywords([...keywords, kw])
      setKeywordInput('')
    }
  }

  async function handleGenerate(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const headers = await getDefaultHeaders()
      const body: Record<string, unknown> = {
        content,
        title,
        generate_featured: generateFeatured,
        generate_social: generateSocial,
        inline_count: inlineCount,
        provider,
        style,
        quality,
      }

      if (keywords.length > 0) body.keywords = keywords

      const res = await fetch(API_ENDPOINTS.images.generateForBlog, {
        method: 'POST',
        headers,
        body: JSON.stringify(body),
      })

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}))
        throw new Error(errData?.detail || errData?.error || `HTTP ${res.status}`)
      }

      const data: BlogImagesResult = await res.json()
      setResult(data)
      showToast({ message: `Generated ${data.total_generated} image${data.total_generated !== 1 ? 's' : ''}!`, variant: 'success' })
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Blog image generation failed.'
      setError(msg)
      showToast({ message: msg, variant: 'error' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <form onSubmit={handleGenerate} className="space-y-6">
        {/* Title */}
        <div>
          <label htmlFor="blog-title" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
            Blog title <span className="text-red-500">*</span>
          </label>
          <input
            id="blog-title"
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Your blog post title"
            className="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-4 py-2.5 text-sm text-gray-900 dark:text-gray-100 placeholder-gray-400 focus:border-amber-500 focus:ring-1 focus:ring-amber-500"
            required
          />
        </div>

        {/* Content */}
        <div>
          <label htmlFor="blog-content" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
            Blog content <span className="text-red-500">*</span>
          </label>
          <textarea
            id="blog-content"
            rows={8}
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Paste your blog content (minimum 10 characters)..."
            className="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-4 py-3 text-sm text-gray-900 dark:text-gray-100 placeholder-gray-400 focus:border-amber-500 focus:ring-1 focus:ring-amber-500"
            required
            minLength={10}
          />
          <p className="mt-1 text-xs text-gray-400">{content.length.toLocaleString()} characters</p>
        </div>

        {/* Keywords */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
            Keywords (optional)
          </label>
          <div className="flex gap-2">
            <input
              type="text"
              value={keywordInput}
              onChange={(e) => setKeywordInput(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); addKeyword() } }}
              placeholder="Add keyword"
              className="flex-1 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-4 py-2.5 text-sm text-gray-900 dark:text-gray-100 placeholder-gray-400 focus:border-amber-500 focus:ring-1 focus:ring-amber-500"
            />
            <button
              type="button"
              onClick={addKeyword}
              disabled={keywords.length >= 20}
              className="px-4 py-2.5 rounded-lg text-sm font-medium bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700 border border-gray-300 dark:border-gray-700 disabled:opacity-50"
            >
              Add
            </button>
          </div>
          {keywords.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-2">
              {keywords.map((kw) => (
                <span
                  key={kw}
                  className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 border border-gray-200 dark:border-gray-700"
                >
                  {kw}
                  <button type="button" onClick={() => setKeywords(keywords.filter((k) => k !== kw))} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">
                    &times;
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Image type toggles */}
        <div className="flex flex-wrap items-center gap-6">
          <label className="inline-flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 cursor-pointer">
            <input
              type="checkbox"
              checked={generateFeatured}
              onChange={(e) => setGenerateFeatured(e.target.checked)}
              className="rounded border-gray-300 text-amber-600 focus:ring-amber-500"
            />
            Featured image
          </label>
          <label className="inline-flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 cursor-pointer">
            <input
              type="checkbox"
              checked={generateSocial}
              onChange={(e) => setGenerateSocial(e.target.checked)}
              className="rounded border-gray-300 text-amber-600 focus:ring-amber-500"
            />
            Social image
          </label>
          <div className="inline-flex items-center gap-2">
            <label htmlFor="inline-count" className="text-sm text-gray-600 dark:text-gray-400">Inline images:</label>
            <select
              id="inline-count"
              value={inlineCount}
              onChange={(e) => setInlineCount(Number(e.target.value))}
              className="rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-1.5 text-sm text-gray-900 dark:text-gray-100 focus:border-amber-500 focus:ring-1 focus:ring-amber-500"
            >
              {[0, 1, 2, 3, 4, 5].map((n) => (
                <option key={n} value={n}>{n}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Style selectors */}
        <StyleSelector
          provider={provider}
          style={style}
          quality={quality}
          size="1024x1024"
          styles={styles}
          onProviderChange={setProvider}
          onStyleChange={setStyle}
          onQualityChange={setQuality}
          onSizeChange={() => {}}
        />

        <button
          type="submit"
          disabled={loading || !title.trim() || content.length < 10}
          className="inline-flex items-center gap-2 px-6 py-3 rounded-lg text-sm font-medium bg-amber-600 text-white hover:bg-amber-700 disabled:bg-gray-300 dark:disabled:bg-gray-700 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Generating...
            </>
          ) : (
            'Generate Blog Images'
          )}
        </button>
      </form>

      {error && (
        <div className="rounded-lg border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20 px-4 py-3 text-sm text-red-700 dark:text-red-300">
          {error}
        </div>
      )}

      {result && (
        <div className="space-y-4">
          <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
            Generated {result.total_generated} image{result.total_generated !== 1 ? 's' : ''}
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {result.featured_image && <ImageCard image={result.featured_image} label="Featured" />}
            {result.social_image && <ImageCard image={result.social_image} label="Social" />}
            {result.inline_images.map((img, i) => (
              <ImageCard key={`inline-${i}`} image={img} label={`Inline ${i + 1}`} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
