'use client'

import React, { memo } from 'react'

interface ProfileSelectorProps {
  profileId: string
  onProfileIdChange: (value: string) => void
  onLoad: () => void
  isLoading?: boolean
}

function ProfileSelectorComponent({
  profileId,
  onProfileIdChange,
  onLoad,
  isLoading = false,
}: ProfileSelectorProps) {
  return (
    <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
      <h2 className="text-lg font-semibold mb-4">Select Brand Profile</h2>
      <div className="flex gap-4">
        <input
          type="text"
          value={profileId}
          onChange={(e) => onProfileIdChange(e.target.value)}
          placeholder="Enter profile ID (e.g., bp-1)"
          className="flex-1 px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-500"
        />
        <button
          onClick={onLoad}
          disabled={!profileId.trim() || isLoading}
          className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-300"
        >
          {isLoading ? 'Loading...' : 'Load'}
        </button>
      </div>
    </div>
  )
}

export const ProfileSelector = memo(ProfileSelectorComponent)
export default ProfileSelector
