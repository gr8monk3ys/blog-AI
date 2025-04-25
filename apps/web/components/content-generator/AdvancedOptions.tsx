import { Switch } from '@headlessui/react'
import { LightBulbIcon } from '@heroicons/react/24/outline'
import BrandVoiceSelector from '../brand/BrandVoiceSelector'
import type { BrandProfile } from '../../types/brand'

interface ToggleOptionProps {
  checked: boolean
  onChange: (value: boolean) => void
  ariaLabel: string
  label: string
  labelId: string
  children?: React.ReactNode
}

function ToggleOption({ checked, onChange, ariaLabel, label, labelId, children }: ToggleOptionProps) {
  return (
    <div className="flex items-center space-x-3">
      <Switch
        checked={checked}
        onChange={onChange}
        aria-label={ariaLabel}
        className={`${
          checked ? 'bg-amber-600' : 'bg-gray-200 dark:bg-gray-700'
        } relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2`}
      >
        <span
          aria-hidden="true"
          className={`${
            checked ? 'translate-x-6' : 'translate-x-1'
          } inline-block h-4 w-4 transform rounded-full bg-white transition-transform`}
        />
      </Switch>
      <span className="text-sm text-gray-700 dark:text-gray-300" id={labelId}>{label}</span>
      {children}
    </div>
  )
}

interface AdvancedOptionsProps {
  useResearch: boolean; onResearchChange: (v: boolean) => void
  researchDepth: 'basic' | 'deep' | 'comprehensive'; onResearchDepthChange: (v: 'basic' | 'deep' | 'comprehensive') => void
  proofread: boolean; onProofreadChange: (v: boolean) => void
  humanize: boolean; onHumanizeChange: (v: boolean) => void
  seoOptimize: boolean; onSeoOptimizeChange: (v: boolean) => void
  factCheck: boolean; onFactCheckChange: (v: boolean) => void
  useKnowledgeBase: boolean; onKnowledgeBaseChange: (v: boolean) => void
  brandVoiceEnabled: boolean; onBrandVoiceEnabledChange: (v: boolean) => void
  selectedBrandProfile: BrandProfile | null; onBrandProfileChange: (p: BrandProfile | null) => void
}

export default function AdvancedOptions({
  useResearch, onResearchChange,
  researchDepth, onResearchDepthChange,
  proofread, onProofreadChange,
  humanize, onHumanizeChange,
  seoOptimize, onSeoOptimizeChange,
  factCheck, onFactCheckChange,
  useKnowledgeBase, onKnowledgeBaseChange,
  brandVoiceEnabled, onBrandVoiceEnabledChange,
  selectedBrandProfile, onBrandProfileChange,
}: AdvancedOptionsProps) {
  return (
    <div className="glass-panel rounded-2xl p-5">
      <div className="flex items-center mb-3">
        <LightBulbIcon className="h-4 w-4 text-amber-600 mr-2" />
        <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">Advanced Options</h3>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <ToggleOption
          checked={useResearch}
          onChange={onResearchChange}
          ariaLabel="Enable web research"
          label="Use web research"
          labelId="research-label"
        >
          {useResearch && (
            <select
              value={researchDepth}
              onChange={(e) => onResearchDepthChange(e.target.value as 'basic' | 'deep' | 'comprehensive')}
              className="ml-2 text-xs rounded border-gray-300 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-100 focus:border-amber-500 focus:ring-amber-500"
            >
              <option value="basic">Basic</option>
              <option value="deep">Deep</option>
              <option value="comprehensive">Comprehensive</option>
            </select>
          )}
        </ToggleOption>

        <ToggleOption
          checked={proofread}
          onChange={onProofreadChange}
          ariaLabel="Enable proofreading"
          label="Proofread content"
          labelId="proofread-label"
        />

        <ToggleOption
          checked={humanize}
          onChange={onHumanizeChange}
          ariaLabel="Enable content humanization"
          label="Humanize content"
          labelId="humanize-label"
        />

        <ToggleOption
          checked={seoOptimize}
          onChange={onSeoOptimizeChange}
          ariaLabel="Enable SEO optimization"
          label="SEO optimize"
          labelId="seo-label"
        />

        <ToggleOption
          checked={factCheck}
          onChange={onFactCheckChange}
          ariaLabel="Enable fact checking"
          label="Fact check"
          labelId="fact-check-label"
        />

        <ToggleOption
          checked={useKnowledgeBase}
          onChange={onKnowledgeBaseChange}
          ariaLabel="Use Knowledge Base"
          label="Use Knowledge Base"
          labelId="kb-label"
        />
      </div>

      <div className="mt-4">
        <BrandVoiceSelector
          enabled={brandVoiceEnabled}
          onEnabledChange={onBrandVoiceEnabledChange}
          selectedProfile={selectedBrandProfile}
          onProfileChange={onBrandProfileChange}
        />
      </div>
    </div>
  )
}
