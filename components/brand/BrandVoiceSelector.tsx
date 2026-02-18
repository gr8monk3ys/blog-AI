'use client'

import { Fragment, useState, useEffect } from 'react'
import { Listbox, Transition, Switch } from '@headlessui/react'
import { ChevronUpDownIcon, CheckIcon } from '@heroicons/react/24/outline'
import { SparklesIcon } from '@heroicons/react/24/solid'
import { BrandProfile, SAMPLE_BRAND_PROFILES } from '../../types/brand'
import { getDefaultHeaders } from '../../lib/api'

interface BrandVoiceSelectorProps {
  enabled: boolean
  onEnabledChange: (enabled: boolean) => void
  selectedProfile: BrandProfile | null
  onProfileChange: (profile: BrandProfile | null) => void
  compact?: boolean
}

export default function BrandVoiceSelector({
  enabled,
  onEnabledChange,
  selectedProfile,
  onProfileChange,
  compact = false,
}: BrandVoiceSelectorProps) {
  const [profiles, setProfiles] = useState<BrandProfile[]>(SAMPLE_BRAND_PROFILES)
  const [loading, setLoading] = useState(false)

  // Fetch profiles from API
  useEffect(() => {
    if (!enabled) return

    const fetchProfiles = async () => {
      setLoading(true)
      try {
        const response = await fetch('/api/brand-profiles?activeOnly=true', {
          headers: await getDefaultHeaders(),
        })
        const data = await response.json()

        if (data.success && data.data.length > 0) {
          setProfiles(data.data)
          // Set default profile if none selected
          if (!selectedProfile) {
            const defaultProfile = data.data.find((p: BrandProfile) => p.isDefault)
            if (defaultProfile) {
              onProfileChange(defaultProfile)
            }
          }
        }
      } catch (error) {
        console.error('Error fetching brand profiles:', error)
        // Fall back to sample data
        setProfiles(SAMPLE_BRAND_PROFILES)
      } finally {
        setLoading(false)
      }
    }

    fetchProfiles()
  }, [enabled, onProfileChange, selectedProfile])

  if (compact) {
    return (
      <div className="flex items-center gap-3">
        <Switch
          checked={enabled}
          onChange={onEnabledChange}
          className={`${
            enabled ? 'bg-amber-600' : 'bg-gray-200'
          } relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2`}
        >
          <span
            className={`${
              enabled ? 'translate-x-6' : 'translate-x-1'
            } inline-block h-4 w-4 transform rounded-full bg-white transition-transform`}
          />
        </Switch>
        <div className="flex items-center gap-1.5">
          <SparklesIcon className="w-4 h-4 text-amber-600" />
          <span className="text-sm text-gray-700">Brand Voice</span>
        </div>
        {enabled && (
          <Listbox value={selectedProfile} onChange={onProfileChange}>
            <div className="relative">
              <Listbox.Button className="relative w-40 cursor-pointer rounded-lg bg-white py-1.5 pl-3 pr-8 text-left border border-gray-300 focus:outline-none focus:ring-2 focus:ring-amber-500 text-sm">
                <span className="block truncate">
                  {selectedProfile?.name || 'Select...'}
                </span>
                <span className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
                  <ChevronUpDownIcon className="h-4 w-4 text-gray-400" />
                </span>
              </Listbox.Button>
              <Transition
                as={Fragment}
                leave="transition ease-in duration-100"
                leaveFrom="opacity-100"
                leaveTo="opacity-0"
              >
                <Listbox.Options className="absolute z-10 mt-1 max-h-60 w-48 overflow-auto rounded-lg bg-white py-1 shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none text-sm">
                  {profiles.map((profile) => (
                    <Listbox.Option
                      key={profile.id}
                      value={profile}
                      className={({ active }) =>
                        `relative cursor-pointer select-none py-2 pl-10 pr-4 ${
                          active ? 'bg-amber-50 text-amber-900' : 'text-gray-900'
                        }`
                      }
                    >
                      {({ selected }) => (
                        <>
                          <span className={`block truncate ${selected ? 'font-medium' : 'font-normal'}`}>
                            {profile.name}
                          </span>
                          {selected && (
                            <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-amber-600">
                              <CheckIcon className="h-4 w-4" />
                            </span>
                          )}
                        </>
                      )}
                    </Listbox.Option>
                  ))}
                </Listbox.Options>
              </Transition>
            </div>
          </Listbox>
        )}
      </div>
    )
  }

  return (
    <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <SparklesIcon className="w-5 h-5 text-amber-600" />
          <h3 className="text-sm font-medium text-gray-900">Apply Brand Voice</h3>
        </div>
        <Switch
          checked={enabled}
          onChange={onEnabledChange}
          className={`${
            enabled ? 'bg-amber-600' : 'bg-gray-200'
          } relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2`}
        >
          <span
            className={`${
              enabled ? 'translate-x-6' : 'translate-x-1'
            } inline-block h-4 w-4 transform rounded-full bg-white transition-transform`}
          />
        </Switch>
      </div>

      {enabled && (
        <div className="space-y-3">
          <Listbox value={selectedProfile} onChange={onProfileChange}>
            <div className="relative">
              <Listbox.Label className="block text-xs text-gray-500 mb-1">
                Select Brand Profile
              </Listbox.Label>
              <Listbox.Button className="relative w-full cursor-pointer rounded-lg bg-white py-2 pl-3 pr-10 text-left border border-gray-300 focus:outline-none focus:ring-2 focus:ring-amber-500 text-sm">
                <span className="block truncate">
                  {selectedProfile?.name || 'Choose a profile...'}
                </span>
                <span className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
                  <ChevronUpDownIcon className="h-5 w-5 text-gray-400" />
                </span>
              </Listbox.Button>
              <Transition
                as={Fragment}
                leave="transition ease-in duration-100"
                leaveFrom="opacity-100"
                leaveTo="opacity-0"
              >
                <Listbox.Options className="absolute z-10 mt-1 max-h-60 w-full overflow-auto rounded-lg bg-white py-1 shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none text-sm">
                  {loading ? (
                    <div className="py-2 px-4 text-gray-500">Loading...</div>
                  ) : profiles.length === 0 ? (
                    <div className="py-2 px-4 text-gray-500">
                      No profiles found.{' '}
                      <a href="/brand" className="text-amber-600 hover:underline">
                        Create one
                      </a>
                    </div>
                  ) : (
                    profiles.map((profile) => (
                      <Listbox.Option
                        key={profile.id}
                        value={profile}
                        className={({ active }) =>
                          `relative cursor-pointer select-none py-2 pl-10 pr-4 ${
                            active ? 'bg-amber-50 text-amber-900' : 'text-gray-900'
                          }`
                        }
                      >
                        {({ selected }) => (
                          <>
                            <div>
                              <span className={`block truncate ${selected ? 'font-medium' : 'font-normal'}`}>
                                {profile.name}
                              </span>
                              <span className="block truncate text-xs text-gray-500 capitalize">
                                {profile.writingStyle} - {profile.toneKeywords.slice(0, 2).join(', ')}
                              </span>
                            </div>
                            {selected && (
                              <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-amber-600">
                                <CheckIcon className="h-5 w-5" />
                              </span>
                            )}
                          </>
                        )}
                      </Listbox.Option>
                    ))
                  )}
                </Listbox.Options>
              </Transition>
            </div>
          </Listbox>

          {selectedProfile && (
            <div className="text-xs text-gray-500 bg-white rounded-lg p-3 border border-gray-200">
              <p className="font-medium text-gray-700 mb-1">Profile Preview:</p>
              <ul className="space-y-1">
                <li>
                  <span className="text-gray-400">Style:</span>{' '}
                  <span className="capitalize">{selectedProfile.writingStyle}</span>
                </li>
                <li>
                  <span className="text-gray-400">Tone:</span>{' '}
                  <span className="capitalize">{selectedProfile.toneKeywords.join(', ')}</span>
                </li>
                {selectedProfile.targetAudience && (
                  <li>
                    <span className="text-gray-400">Audience:</span>{' '}
                    {selectedProfile.targetAudience}
                  </li>
                )}
              </ul>
            </div>
          )}
        </div>
      )}

      {!enabled && (
        <p className="text-xs text-gray-500">
          Enable to apply your brand&apos;s tone and style to generated content.
        </p>
      )}
    </div>
  )
}
