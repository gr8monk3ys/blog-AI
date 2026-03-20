'use client'

import type { ImageProvider, ImageStyle, ImageQuality, ImageSize, ImageStylesResponse } from '../../../types/images'

interface StyleSelectorProps {
  provider: ImageProvider
  style: ImageStyle
  quality: ImageQuality
  size: ImageSize
  styles: ImageStylesResponse | null
  onProviderChange: (v: ImageProvider) => void
  onStyleChange: (v: ImageStyle) => void
  onQualityChange: (v: ImageQuality) => void
  onSizeChange: (v: ImageSize) => void
}

const DEFAULT_SIZES: ImageSize[] = ['1024x1024', '1792x1024', '1024x1792']

export default function StyleSelector({
  provider,
  style,
  quality,
  size,
  styles,
  onProviderChange,
  onStyleChange,
  onQualityChange,
  onSizeChange,
}: StyleSelectorProps) {
  const providers = styles?.providers || ['openai', 'stability']
  const sizes = styles?.sizes?.[provider] || DEFAULT_SIZES
  const qualities: ImageQuality[] = styles?.qualities || ['standard', 'hd']

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
      <div>
        <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Provider</label>
        <select
          value={provider}
          onChange={(e) => onProviderChange(e.target.value as ImageProvider)}
          className="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:border-amber-500 focus:ring-1 focus:ring-amber-500"
        >
          {providers.map((p) => (
            <option key={p} value={p} className="capitalize">{p === 'openai' ? 'DALL-E 3' : 'Stability AI'}</option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Style</label>
        <select
          value={style}
          onChange={(e) => onStyleChange(e.target.value as ImageStyle)}
          className="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:border-amber-500 focus:ring-1 focus:ring-amber-500"
        >
          <option value="natural">Natural</option>
          <option value="vivid">Vivid</option>
        </select>
      </div>

      <div>
        <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Quality</label>
        <select
          value={quality}
          onChange={(e) => onQualityChange(e.target.value as ImageQuality)}
          className="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:border-amber-500 focus:ring-1 focus:ring-amber-500"
        >
          {qualities.map((q) => (
            <option key={q} value={q} className="capitalize">{q === 'hd' ? 'HD' : 'Standard'}</option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Size</label>
        <select
          value={size}
          onChange={(e) => onSizeChange(e.target.value as ImageSize)}
          className="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:border-amber-500 focus:ring-1 focus:ring-amber-500"
        >
          {sizes.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
      </div>
    </div>
  )
}
