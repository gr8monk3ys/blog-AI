'use client'

import { Switch } from '@headlessui/react'
import {
  LightBulbIcon,
  BeakerIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline'

interface AdvancedOptionsProps {
  useResearch: boolean
  onUseResearchChange: (value: boolean) => void
  generateVariations: boolean
  onGenerateVariationsChange: (value: boolean) => void
  variationCount: number
  onVariationCountChange: (value: number) => void
  keywords: string
  onKeywordsChange: (value: string) => void
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
}: AdvancedOptionsProps) {
  return (
    <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
      <div className="flex items-center mb-3">
        <LightBulbIcon
          className="h-4 w-4 text-indigo-600 mr-2"
          aria-hidden="true"
        />
        <h3 className="text-sm font-medium text-gray-700">Advanced Options</h3>
      </div>

      <div className="space-y-4">
        {/* Web research toggle */}
        <div className="flex items-center space-x-3">
          <Switch
            checked={useResearch}
            onChange={onUseResearchChange}
            aria-label="Use web research"
            className={`${
              useResearch ? 'bg-indigo-600' : 'bg-gray-200'
            } relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2`}
          >
            <span
              aria-hidden="true"
              className={`${
                useResearch ? 'translate-x-6' : 'translate-x-1'
              } inline-block h-4 w-4 transform rounded-full bg-white transition-transform`}
            />
          </Switch>
          <span className="text-sm text-gray-700">
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
                generateVariations ? 'bg-indigo-600' : 'bg-gray-200'
              } relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2`}
            >
              <span
                aria-hidden="true"
                className={`${
                  generateVariations ? 'translate-x-6' : 'translate-x-1'
                } inline-block h-4 w-4 transform rounded-full bg-white transition-transform`}
              />
            </Switch>
            <div className="flex items-center gap-2">
              <BeakerIcon className="w-4 h-4 text-indigo-600" />
              <span className="text-sm text-gray-700">
                Generate variations for A/B testing
              </span>
            </div>
          </div>
          {generateVariations && (
            <select
              value={variationCount}
              onChange={(e) => onVariationCountChange(Number(e.target.value))}
              className="text-sm rounded-md border-gray-300 focus:border-indigo-500 focus:ring-indigo-500"
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
            className="flex items-center gap-2 text-sm text-gray-700 mb-1"
          >
            <ChartBarIcon className="w-4 h-4 text-indigo-600" />
            Keywords for SEO scoring (comma-separated)
          </label>
          <input
            type="text"
            id="keywords"
            value={keywords}
            onChange={(e) => onKeywordsChange(e.target.value)}
            placeholder="e.g., AI, machine learning, technology"
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
          />
        </div>
      </div>
    </div>
  )
}
