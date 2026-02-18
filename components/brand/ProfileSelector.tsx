'use client'

import React, { memo, useEffect, useState } from 'react'
import Link from 'next/link'
import type { BrandProfile } from '../../types/brand'
import { SAMPLE_BRAND_PROFILES } from '../../types/brand'
import { getDefaultHeaders } from '../../lib/api'

interface ProfileSelectorProps {
  profileId: string
  onProfileIdChange: (value: string) => void
  onLoad: (profileId: string) => void
  isLoading?: boolean
}

function ProfileSelectorComponent({
  profileId,
  onProfileIdChange,
  onLoad,
  isLoading = false,
}: ProfileSelectorProps) {
  const [profiles, setProfiles] = useState<BrandProfile[]>([])
  const [loadingProfiles, setLoadingProfiles] = useState(false)

  useEffect(() => {
    const fetchProfiles = async () => {
      setLoadingProfiles(true)
      try {
        const response = await fetch('/api/brand-profiles?activeOnly=true', {
          headers: await getDefaultHeaders(),
        })
        const data = await response.json().catch(() => ({}))

        if (data?.success && Array.isArray(data?.data)) {
          setProfiles(data.data)

          // Auto-select default profile on first load.
          if (!profileId) {
            const defaultProfile =
              data.data.find((p: BrandProfile) => p.isDefault) || data.data[0]
            if (defaultProfile?.id) {
              onProfileIdChange(defaultProfile.id)
              onLoad(defaultProfile.id)
            }
          }
          return
        }
      } catch {
        // Ignore and fallback
      } finally {
        setLoadingProfiles(false)
      }

      // Fallback to sample profiles (IDs are UUIDs, so backend validation still works in dev).
      setProfiles(SAMPLE_BRAND_PROFILES)
      if (!profileId && SAMPLE_BRAND_PROFILES.length > 0) {
        const defaultProfile =
          SAMPLE_BRAND_PROFILES.find((p) => p.isDefault) || SAMPLE_BRAND_PROFILES[0]
        if (defaultProfile?.id) {
          onProfileIdChange(defaultProfile.id)
          onLoad(defaultProfile.id)
        }
      }
    }

    fetchProfiles()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
      <h2 className="text-lg font-semibold mb-4">Select Brand Profile</h2>
      <div className="flex gap-4">
        <select
          value={profileId}
          onChange={(e) => {
            const id = e.target.value
            onProfileIdChange(id)
            if (id) onLoad(id)
          }}
          disabled={loadingProfiles}
          className="flex-1 px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-amber-500 bg-white"
        >
          <option value="">
            {loadingProfiles ? 'Loading profiles...' : 'Select a profile...'}
          </option>
          {profiles.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>
        <button
          onClick={() => onLoad(profileId)}
          disabled={!profileId.trim() || isLoading}
          className="px-6 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 disabled:bg-gray-300"
        >
          {isLoading ? 'Loading...' : 'Load'}
        </button>
      </div>

      {profiles.length === 0 && !loadingProfiles && (
        <p className="mt-3 text-sm text-gray-500">
          No brand profiles yet.{' '}
          <Link href="/brand" className="text-amber-600 hover:underline">
            Create one
          </Link>
        </p>
      )}
    </div>
  )
}

export const ProfileSelector = memo(ProfileSelectorComponent)
export default ProfileSelector
