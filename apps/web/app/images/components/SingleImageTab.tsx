'use client'

import { useState } from 'react'
import { API_ENDPOINTS, getDefaultHeaders } from '../../../lib/api'
import type { ToastOptions } from '../../../hooks/useToast'
import type { ImageResult, ImageProvider, ImageStyle, ImageQuality, ImageSize, ImageType, ImageStylesResponse } from '../../../types/images'
import StyleSelector from './StyleSelector'
import ImageCard from './ImageCard'

interface SingleImageTabProps {
  styles: ImageStylesResponse | null
  showToast: (opts: ToastOptions) => void
}

const IMAGE_TYPES: { value: ImageType; label: string }[] = [
  { value: 'featured', label: 'Featured image' },
  { value: 'social', label: 'Social media' },
  { value: 'inline', label: 'Inline illustration' },
  { value: 'thumbnail', label: 'Thumbnail' },
  { value: 'hero', label: 'Hero banner' },
]

export default function SingleImageTab({ styles, showToast }: SingleImageTabProps) {
  const [mode, setMode] = useState<'content' | 'prompt'>('prompt')
  const [prompt, setPrompt] = useState('')
  const [content, setContent] = useState('')
  const [imageType, setImageType] = useState<ImageType>('featured')
  const [provider, setProvider] = useState<ImageProvider>('openai')
  const [style, setStyle] = useState<ImageStyle>('natural')
  const [quality, setQuality] = useState<ImageQuality>('standard')
  const [size, setSize] = useState<ImageSize>('1024x1024')
  const [negativePrompt, setNegativePrompt] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<ImageResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function handleGenerate(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const headers = await getDefaultHeaders()
      const body: Record<string, unknown> = {
        image_type: imageType,
        size,
        style,
        quality,
        provider,
      }

      if (mode === 'prompt') {
        body.custom_prompt = prompt
      } else {
        body.content = content
      }

      if (negativePrompt) body.negative_prompt = negativePrompt

      const res = await fetch(API_ENDPOINTS.images.generate, {
        method: 'POST',
        headers,
        body: JSON.stringify(body),
      })

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}))
        throw new Error(errData?.detail || errData?.error || `HTTP ${res.status}`)
      }

      const data: ImageResult = await res.json()
      setResult(data)
      showToast({ message: 'Image generated!', variant: 'success' })
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Image generation failed.'
      setError(msg)
      showToast({ message: msg, variant: 'error' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <form onSubmit={handleGenerate} className="space-y-6">
        {/* Mode toggle */}
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setMode('prompt')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              mode === 'prompt'
                ? 'bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-300'
                : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'
            }`}
          >
            Custom Prompt
          </button>
          <button
            type="button"
            onClick={() => setMode('content')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              mode === 'content'
                ? 'bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-300'
                : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'
            }`}
          >
            From Content
          </button>
        </div>

        {/* Input */}
        {mode === 'prompt' ? (
          <div>
            <label htmlFor="img-prompt" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
              Image prompt <span className="text-red-500">*</span>
            </label>
            <textarea
              id="img-prompt"
              rows={4}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Describe the image you want to generate..."
              className="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-4 py-3 text-sm text-gray-900 dark:text-gray-100 placeholder-gray-400 focus:border-amber-500 focus:ring-1 focus:ring-amber-500"
              required
            />
          </div>
        ) : (
          <div>
            <label htmlFor="img-content" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
              Content <span className="text-red-500">*</span>
            </label>
            <textarea
              id="img-content"
              rows={6}
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Paste your blog content and we'll generate a relevant image..."
              className="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-4 py-3 text-sm text-gray-900 dark:text-gray-100 placeholder-gray-400 focus:border-amber-500 focus:ring-1 focus:ring-amber-500"
              required
            />
          </div>
        )}

        {/* Image type */}
        <div>
          <label htmlFor="img-type" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
            Image type
          </label>
          <select
            id="img-type"
            value={imageType}
            onChange={(e) => setImageType(e.target.value as ImageType)}
            className="w-full sm:w-auto rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-4 py-2.5 text-sm text-gray-900 dark:text-gray-100 focus:border-amber-500 focus:ring-1 focus:ring-amber-500"
          >
            {IMAGE_TYPES.map((t) => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>
        </div>

        {/* Style selectors */}
        <StyleSelector
          provider={provider}
          style={style}
          quality={quality}
          size={size}
          styles={styles}
          onProviderChange={setProvider}
          onStyleChange={setStyle}
          onQualityChange={setQuality}
          onSizeChange={setSize}
        />

        {/* Negative prompt */}
        <div>
          <label htmlFor="neg-prompt" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
            Negative prompt (optional)
          </label>
          <input
            id="neg-prompt"
            type="text"
            value={negativePrompt}
            onChange={(e) => setNegativePrompt(e.target.value)}
            placeholder="Elements to exclude from the image..."
            className="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-4 py-2.5 text-sm text-gray-900 dark:text-gray-100 placeholder-gray-400 focus:border-amber-500 focus:ring-1 focus:ring-amber-500"
          />
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={loading || (mode === 'prompt' ? !prompt.trim() : !content.trim())}
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
            'Generate Image'
          )}
        </button>
      </form>

      {error && (
        <div className="rounded-lg border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20 px-4 py-3 text-sm text-red-700 dark:text-red-300">
          {error}
        </div>
      )}

      {result && (
        <div className="max-w-md">
          <ImageCard image={result} />
        </div>
      )}
    </div>
  )
}
