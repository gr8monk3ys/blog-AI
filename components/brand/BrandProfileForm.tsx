'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  BrandProfile,
  ToneKeyword,
  WritingStyle,
  Industry,
  WRITING_STYLES,
  TONE_KEYWORDS,
  INDUSTRIES,
} from '../../types/brand'
import {
  SparklesIcon,
  XMarkIcon,
  PlusIcon,
} from '@heroicons/react/24/outline'

interface BrandProfileFormProps {
  profile?: BrandProfile | null
  onSubmit: (data: BrandProfileFormData) => Promise<void>
  onCancel?: () => void
  isLoading?: boolean
}

export interface BrandProfileFormData {
  name: string
  toneKeywords: ToneKeyword[]
  writingStyle: WritingStyle
  exampleContent: string
  industry: Industry | null
  targetAudience: string
  preferredWords: string[]
  avoidWords: string[]
  brandValues: string[]
  contentThemes: string[]
}

export default function BrandProfileForm({
  profile,
  onSubmit,
  onCancel,
  isLoading = false,
}: BrandProfileFormProps) {
  const [name, setName] = useState(profile?.name || '')
  const [toneKeywords, setToneKeywords] = useState<ToneKeyword[]>(
    profile?.toneKeywords || []
  )
  const [writingStyle, setWritingStyle] = useState<WritingStyle>(
    profile?.writingStyle || 'balanced'
  )
  const [exampleContent, setExampleContent] = useState(
    profile?.exampleContent || ''
  )
  const [industry, setIndustry] = useState<Industry | null>(
    profile?.industry || null
  )
  const [targetAudience, setTargetAudience] = useState(
    profile?.targetAudience || ''
  )
  const [preferredWords, setPreferredWords] = useState<string[]>(
    profile?.preferredWords || []
  )
  const [avoidWords, setAvoidWords] = useState<string[]>(
    profile?.avoidWords || []
  )
  const [brandValues, setBrandValues] = useState<string[]>(
    profile?.brandValues || []
  )
  const [contentThemes, setContentThemes] = useState<string[]>(
    profile?.contentThemes || []
  )
  const [error, setError] = useState<string | null>(null)

  // Input states for array fields
  const [preferredWordInput, setPreferredWordInput] = useState('')
  const [avoidWordInput, setAvoidWordInput] = useState('')
  const [brandValueInput, setBrandValueInput] = useState('')
  const [contentThemeInput, setContentThemeInput] = useState('')

  // Update form when profile changes
  useEffect(() => {
    if (profile) {
      setName(profile.name)
      setToneKeywords(profile.toneKeywords)
      setWritingStyle(profile.writingStyle)
      setExampleContent(profile.exampleContent || '')
      setIndustry(profile.industry || null)
      setTargetAudience(profile.targetAudience || '')
      setPreferredWords(profile.preferredWords)
      setAvoidWords(profile.avoidWords)
      setBrandValues(profile.brandValues)
      setContentThemes(profile.contentThemes)
    }
  }, [profile])

  const handleToneToggle = (keyword: ToneKeyword) => {
    setToneKeywords((prev) =>
      prev.includes(keyword)
        ? prev.filter((k) => k !== keyword)
        : [...prev, keyword]
    )
  }

  const addToArray = (
    value: string,
    setter: React.Dispatch<React.SetStateAction<string[]>>,
    inputSetter: React.Dispatch<React.SetStateAction<string>>
  ) => {
    const trimmed = value.trim()
    if (trimmed) {
      setter((prev) => (prev.includes(trimmed) ? prev : [...prev, trimmed]))
      inputSetter('')
    }
  }

  const removeFromArray = (
    value: string,
    setter: React.Dispatch<React.SetStateAction<string[]>>
  ) => {
    setter((prev) => prev.filter((v) => v !== value))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!name.trim()) {
      setError('Profile name is required')
      return
    }

    if (toneKeywords.length === 0) {
      setError('Please select at least one tone keyword')
      return
    }

    try {
      await onSubmit({
        name: name.trim(),
        toneKeywords,
        writingStyle,
        exampleContent: exampleContent.trim(),
        industry,
        targetAudience: targetAudience.trim(),
        preferredWords,
        avoidWords,
        brandValues,
        contentThemes,
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save profile')
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {error && (
        <div className="p-4 rounded-lg bg-red-50 text-sm text-red-600 border border-red-100">
          {error}
        </div>
      )}

      {/* Profile Name */}
      <div>
        <label
          htmlFor="profile-name"
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          Profile Name *
        </label>
        <input
          type="text"
          id="profile-name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g., Tech Startup Voice"
          className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
          required
        />
      </div>

      {/* Writing Style */}
      <div>
        <label
          htmlFor="writing-style"
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          Writing Style
        </label>
        <select
          id="writing-style"
          value={writingStyle}
          onChange={(e) => setWritingStyle(e.target.value as WritingStyle)}
          className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
        >
          {WRITING_STYLES.map((style) => (
            <option key={style.value} value={style.value}>
              {style.label} - {style.description}
            </option>
          ))}
        </select>
      </div>

      {/* Tone Keywords */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Tone Keywords * (select multiple)
        </label>
        <div className="flex flex-wrap gap-2">
          {TONE_KEYWORDS.map((keyword) => (
            <button
              key={keyword.value}
              type="button"
              onClick={() => handleToneToggle(keyword.value)}
              className={`inline-flex items-center px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                toneKeywords.includes(keyword.value)
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {keyword.label}
            </button>
          ))}
        </div>
      </div>

      {/* Industry */}
      <div>
        <label
          htmlFor="industry"
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          Industry
        </label>
        <select
          id="industry"
          value={industry || ''}
          onChange={(e) => setIndustry((e.target.value as Industry) || null)}
          className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
        >
          <option value="">Select an industry...</option>
          {INDUSTRIES.map((ind) => (
            <option key={ind.value} value={ind.value}>
              {ind.label}
            </option>
          ))}
        </select>
      </div>

      {/* Target Audience */}
      <div>
        <label
          htmlFor="target-audience"
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          Target Audience
        </label>
        <textarea
          id="target-audience"
          value={targetAudience}
          onChange={(e) => setTargetAudience(e.target.value)}
          placeholder="Describe your ideal reader or customer..."
          rows={2}
          className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
        />
      </div>

      {/* Example Content */}
      <div>
        <label
          htmlFor="example-content"
          className="block text-sm font-medium text-gray-700 mb-1"
        >
          Example Content
        </label>
        <p className="text-xs text-gray-500 mb-2">
          Paste an example of your ideal brand voice for the AI to learn from.
        </p>
        <textarea
          id="example-content"
          value={exampleContent}
          onChange={(e) => setExampleContent(e.target.value)}
          placeholder="Paste a paragraph that exemplifies your brand voice..."
          rows={4}
          className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
        />
      </div>

      {/* Preferred Words */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Preferred Words & Phrases
        </label>
        <div className="flex gap-2 mb-2">
          <input
            type="text"
            value={preferredWordInput}
            onChange={(e) => setPreferredWordInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault()
                addToArray(preferredWordInput, setPreferredWords, setPreferredWordInput)
              }
            }}
            placeholder="Add a word or phrase..."
            className="flex-1 rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
          />
          <button
            type="button"
            onClick={() =>
              addToArray(preferredWordInput, setPreferredWords, setPreferredWordInput)
            }
            className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 bg-white hover:bg-gray-50"
          >
            <PlusIcon className="w-4 h-4" />
          </button>
        </div>
        <div className="flex flex-wrap gap-1">
          {preferredWords.map((word) => (
            <span
              key={word}
              className="inline-flex items-center gap-1 px-2 py-1 rounded text-xs bg-emerald-50 text-emerald-700 border border-emerald-100"
            >
              {word}
              <button
                type="button"
                onClick={() => removeFromArray(word, setPreferredWords)}
                className="hover:text-emerald-900"
              >
                <XMarkIcon className="w-3 h-3" />
              </button>
            </span>
          ))}
        </div>
      </div>

      {/* Avoid Words */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Words to Avoid
        </label>
        <div className="flex gap-2 mb-2">
          <input
            type="text"
            value={avoidWordInput}
            onChange={(e) => setAvoidWordInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault()
                addToArray(avoidWordInput, setAvoidWords, setAvoidWordInput)
              }
            }}
            placeholder="Add a word to avoid..."
            className="flex-1 rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
          />
          <button
            type="button"
            onClick={() =>
              addToArray(avoidWordInput, setAvoidWords, setAvoidWordInput)
            }
            className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 bg-white hover:bg-gray-50"
          >
            <PlusIcon className="w-4 h-4" />
          </button>
        </div>
        <div className="flex flex-wrap gap-1">
          {avoidWords.map((word) => (
            <span
              key={word}
              className="inline-flex items-center gap-1 px-2 py-1 rounded text-xs bg-red-50 text-red-700 border border-red-100"
            >
              {word}
              <button
                type="button"
                onClick={() => removeFromArray(word, setAvoidWords)}
                className="hover:text-red-900"
              >
                <XMarkIcon className="w-3 h-3" />
              </button>
            </span>
          ))}
        </div>
      </div>

      {/* Brand Values */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Brand Values
        </label>
        <div className="flex gap-2 mb-2">
          <input
            type="text"
            value={brandValueInput}
            onChange={(e) => setBrandValueInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault()
                addToArray(brandValueInput, setBrandValues, setBrandValueInput)
              }
            }}
            placeholder="e.g., Innovation, Transparency..."
            className="flex-1 rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
          />
          <button
            type="button"
            onClick={() =>
              addToArray(brandValueInput, setBrandValues, setBrandValueInput)
            }
            className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 bg-white hover:bg-gray-50"
          >
            <PlusIcon className="w-4 h-4" />
          </button>
        </div>
        <div className="flex flex-wrap gap-1">
          {brandValues.map((value) => (
            <span
              key={value}
              className="inline-flex items-center gap-1 px-2 py-1 rounded text-xs bg-purple-50 text-purple-700 border border-purple-100"
            >
              {value}
              <button
                type="button"
                onClick={() => removeFromArray(value, setBrandValues)}
                className="hover:text-purple-900"
              >
                <XMarkIcon className="w-3 h-3" />
              </button>
            </span>
          ))}
        </div>
      </div>

      {/* Content Themes */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Content Themes
        </label>
        <div className="flex gap-2 mb-2">
          <input
            type="text"
            value={contentThemeInput}
            onChange={(e) => setContentThemeInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault()
                addToArray(contentThemeInput, setContentThemes, setContentThemeInput)
              }
            }}
            placeholder="e.g., Future of work, Team collaboration..."
            className="flex-1 rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
          />
          <button
            type="button"
            onClick={() =>
              addToArray(contentThemeInput, setContentThemes, setContentThemeInput)
            }
            className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 bg-white hover:bg-gray-50"
          >
            <PlusIcon className="w-4 h-4" />
          </button>
        </div>
        <div className="flex flex-wrap gap-1">
          {contentThemes.map((theme) => (
            <span
              key={theme}
              className="inline-flex items-center gap-1 px-2 py-1 rounded text-xs bg-blue-50 text-blue-700 border border-blue-100"
            >
              {theme}
              <button
                type="button"
                onClick={() => removeFromArray(theme, setContentThemes)}
                className="hover:text-blue-900"
              >
                <XMarkIcon className="w-3 h-3" />
              </button>
            </span>
          ))}
        </div>
      </div>

      {/* Actions */}
      <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 transition-colors"
          >
            Cancel
          </button>
        )}
        <button
          type="submit"
          disabled={isLoading}
          className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <SparklesIcon className="w-4 h-4" />
          {isLoading ? 'Saving...' : profile ? 'Update Profile' : 'Create Profile'}
        </button>
      </div>
    </form>
  )
}
