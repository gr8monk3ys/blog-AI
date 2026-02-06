'use client'

import { SparklesIcon } from '@heroicons/react/24/outline'
import BrandVoiceSelector from '../../brand/BrandVoiceSelector'
import AdvancedOptions from './AdvancedOptions'
import { getInputLabel, getInputPlaceholder } from './utils'
import { TONE_OPTIONS } from './types'
import type { Tool } from '../../../types/tools'
import type { BrandProfile } from '../../../types/brand'

interface ToolInputFormProps {
  tool: Tool
  inputText: string
  onInputTextChange: (value: string) => void
  tone: string
  onToneChange: (value: string) => void
  useResearch: boolean
  onUseResearchChange: (value: boolean) => void
  generateVariations: boolean
  onGenerateVariationsChange: (value: boolean) => void
  variationCount: number
  onVariationCountChange: (value: number) => void
  keywords: string
  onKeywordsChange: (value: string) => void
  brandVoiceEnabled: boolean
  onBrandVoiceEnabledChange: (value: boolean) => void
  selectedBrandProfile: BrandProfile | null
  onSelectedBrandProfileChange: (value: BrandProfile | null) => void
  loading: boolean
  onSubmit: (e: React.FormEvent) => void
}

/**
 * Loading spinner for the submit button
 */
function LoadingSpinner() {
  return (
    <svg
      className="animate-spin -ml-1 mr-2 h-4 w-4 text-white"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
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
  )
}

/**
 * Main input form for content generation
 * Renders the form fields without outer wrapper (wrapper provided by parent)
 */
export default function ToolInputForm({
  tool,
  inputText,
  onInputTextChange,
  tone,
  onToneChange,
  useResearch,
  onUseResearchChange,
  generateVariations,
  onGenerateVariationsChange,
  variationCount,
  onVariationCountChange,
  keywords,
  onKeywordsChange,
  brandVoiceEnabled,
  onBrandVoiceEnabledChange,
  selectedBrandProfile,
  onSelectedBrandProfileChange,
  loading,
  onSubmit,
}: ToolInputFormProps) {
  return (
    <div className="p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">
        Create Content
      </h2>

      <form onSubmit={onSubmit} className="space-y-5">
        {/* Main input */}
        <div>
          <label
            htmlFor="input"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            {getInputLabel(tool)}
          </label>
          <textarea
            id="input"
            value={inputText}
            onChange={(e) => onInputTextChange(e.target.value)}
            rows={4}
            className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
            placeholder={getInputPlaceholder(tool)}
            required
          />
        </div>

        {/* Tone selector */}
        <div>
          <label
            htmlFor="tone"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Tone
          </label>
          <select
            id="tone"
            value={tone}
            onChange={(e) => onToneChange(e.target.value)}
            className="block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
          >
            {TONE_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        {/* Advanced options */}
        <AdvancedOptions
          useResearch={useResearch}
          onUseResearchChange={onUseResearchChange}
          generateVariations={generateVariations}
          onGenerateVariationsChange={onGenerateVariationsChange}
          variationCount={variationCount}
          onVariationCountChange={onVariationCountChange}
          keywords={keywords}
          onKeywordsChange={onKeywordsChange}
        />

        {/* Brand Voice Selector */}
        <BrandVoiceSelector
          enabled={brandVoiceEnabled}
          onEnabledChange={onBrandVoiceEnabledChange}
          selectedProfile={selectedBrandProfile}
          onProfileChange={onSelectedBrandProfileChange}
        />

        {/* Submit button */}
        <button
          type="submit"
          disabled={loading || !inputText.trim()}
          className="w-full flex justify-center items-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-gradient-to-r from-indigo-600 to-indigo-700 hover:from-indigo-700 hover:to-indigo-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? (
            <>
              <LoadingSpinner />
              Generating...
            </>
          ) : (
            <>
              <SparklesIcon className="w-4 h-4 mr-2" aria-hidden="true" />
              Generate Content
            </>
          )}
        </button>
      </form>
    </div>
  )
}
