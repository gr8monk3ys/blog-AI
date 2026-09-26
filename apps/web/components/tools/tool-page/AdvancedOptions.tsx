'use client'

import { Switch } from '@headlessui/react'
import {
  LightBulbIcon,
  BeakerIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline'
import type { LlmProviderType } from '../../../types/llm'

interface AdvancedOptionsProps {
  useResearch: boolean
  onUseResearchChange: (value: boolean) => void
  generateVariations: boolean
  onGenerateVariationsChange: (value: boolean) => void
  variationCount: number
  onVariationCountChange: (value: number) => void
  keywords: string
  onKeywordsChange: (value: string) => void
  providerType: LlmProviderType
  availableProviders: LlmProviderType[]
  onProviderTypeChange: (value: LlmProviderType) => void
}

/**
 * Advanced options section for content generation settings
 */
export default function AdvancedOptions({
  useResearch,
  onUseResearchChange,
  generateVariations,
  onGenerateVariationsChange,
  variationCount,
  onVariationCountChange,
  keywords,
  onKeywordsChange,
  providerType,
  availableProviders,
  onProviderTypeChange,
}: AdvancedOptionsProps) {
  return (
    <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-4 border border-gray-200 dark:border-gray-800">
      <div className="flex items-center mb-3">
        <LightBulbIcon
          className="h-4 w-4 text-amber-700 dark:text-amber-400 mr-2"
          aria-hidden="true"
        />
        <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">Advanced Options</h3>
      </div>

      <div className="space-y-4">
        {/* Web research toggle */}
        <div className="flex items-center space-x-3">
          <Switch
            checked={useResearch}
            onChange={onUseResearchChange}
            aria-label="Use web research"
            className={`${
              useResearch ? 'bg-amber-600' : 'bg-gray-200 dark:bg-gray-700'
            } relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-500 focus-visible:ring-offset-2`}
          >
            <span
              aria-hidden="true"
              className={`${
                useResearch ? 'translate-x-6' : 'translate-x-1'
              } inline-block h-4 w-4 transform rounded-full bg-white transition-transform`}
            />
          </Switch>
          <span className="text-sm text-gray-700 dark:text-gray-300">
            Use web research for better results
          </span>
        </div>

        {/* A/B Testing toggle */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Switch
              checked={generateVariations}
              onChange={onGenerateVariationsChange}
              aria-label="Generate variations"
              className={`${
                generateVariations ? 'bg-amber-600' : 'bg-gray-200 dark:bg-gray-700'
              } relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-500 focus-visible:ring-offset-2`}
            >
              <span
                aria-hidden="true"
                className={`${
                  generateVariations ? 'translate-x-6' : 'translate-x-1'
                } inline-block h-4 w-4 transform rounded-full bg-white transition-transform`}
              />
            </Switch>
            <div className="flex items-center gap-2">
              <BeakerIcon aria-hidden="true" className="w-4 h-4 text-amber-700 dark:text-amber-400" />
              <span className="text-sm text-gray-700 dark:text-gray-300">
                Generate variations for A/B testing
              </span>
            </div>
          </div>
          {generateVariations && (
            <select
              name="variationCount"
              value={variationCount}
              onChange={(e) => onVariationCountChange(Number(e.target.value))}
              className="text-sm rounded-md border-gray-300 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-100 focus-visible:border-amber-500 focus-visible:ring-amber-500"
            >
              <option value={2}>2 versions</option>
              <option value={3}>3 versions</option>
            </select>
          )}
        </div>

        {/* Keywords input for SEO scoring */}
        <div>
          <label
            htmlFor="keywords"
            className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300 mb-1"
          >
            <ChartBarIcon aria-hidden="true" className="w-4 h-4 text-amber-700 dark:text-amber-400" />
            Keywords for SEO scoring (comma-separated)
          </label>
          <input
            name="keywords"
            autoComplete="off"
            type="text"
            id="keywords"
            value={keywords}
            onChange={(e) => onKeywordsChange(e.target.value)}
            placeholder="e.g. AI, machine learning, technology…"
            className="block w-full rounded-md border-gray-300 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-100 dark:placeholder-gray-500 shadow-sm focus-visible:border-amber-500 focus-visible:ring-amber-500 text-sm"
          />
        </div>

        {/* Provider selection */}
        <div>
          <label
            htmlFor="provider"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
          >
            Model Provider
          </label>
          <select
            name="provider"
            id="provider"
            value={providerType}
            onChange={(e) => onProviderTypeChange(e.target.value as LlmProviderType)}
            className="block w-full rounded-md border-gray-300 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-100 shadow-sm focus-visible:border-amber-500 focus-visible:ring-amber-500 text-sm"
            disabled={(availableProviders || []).length <= 1}
          >
            {(availableProviders || []).map((p) => (
              <option key={p} value={p}>
                {p === 'openai' ? 'OpenAI' : p === 'anthropic' ? 'Anthropic' : 'Gemini'}
              </option>
            ))}
          </select>
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            Uses whichever providers are configured on the server.
          </p>
        </div>
      </div>
    </div>
  )
}
