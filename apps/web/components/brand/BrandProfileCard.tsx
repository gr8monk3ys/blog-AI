'use client'

import { motion } from 'framer-motion'
import { BrandProfile, INDUSTRIES } from '../../types/brand'
import {
  CheckCircleIcon,
  StarIcon,
  PencilSquareIcon,
  TrashIcon,
} from '@heroicons/react/24/outline'
import { StarIcon as StarIconSolid } from '@heroicons/react/24/solid'

interface BrandProfileCardProps {
  profile: BrandProfile
  index?: number
  onEdit?: (profile: BrandProfile) => void
  onDelete?: (profile: BrandProfile) => void
  onSetDefault?: (profile: BrandProfile) => void
}

export default function BrandProfileCard({
  profile,
  index = 0,
  onEdit,
  onDelete,
  onSetDefault,
}: BrandProfileCardProps) {
  const industryLabel = profile.industry
    ? INDUSTRIES.find((i) => i.value === profile.industry)?.label || profile.industry
    : null

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.05 }}
      className={`relative bg-white dark:bg-gray-900 rounded-xl border shadow-sm hover:shadow-md transition-all duration-200 overflow-hidden ${
        profile.isDefault ? 'border-amber-300 dark:border-amber-700 ring-2 ring-amber-100 dark:ring-amber-900/50' : 'border-gray-200 dark:border-gray-800'
      }`}
    >
      {/* Default badge */}
      {profile.isDefault && (
        <div className="absolute top-3 right-3">
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800">
            <StarIconSolid className="w-3 h-3" />
            Default
          </span>
        </div>
      )}

      <div className="p-5">
        {/* Profile name and status */}
        <div className="flex items-start gap-3 mb-4">
          <div
            className={`flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center ${
              profile.isActive ? 'bg-emerald-100 dark:bg-emerald-900/30' : 'bg-gray-100 dark:bg-gray-800'
            }`}
          >
            <CheckCircleIcon
              className={`w-5 h-5 ${profile.isActive ? 'text-emerald-600 dark:text-emerald-400' : 'text-gray-400'}`}
            />
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="text-base font-semibold text-gray-900 dark:text-gray-100 truncate">
              {profile.name}
            </h3>
            {industryLabel && (
              <p className="text-sm text-gray-500 dark:text-gray-400">{industryLabel}</p>
            )}
          </div>
        </div>

        {/* Writing style */}
        <div className="mb-4">
          <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Writing Style</p>
          <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium bg-amber-50 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 border border-amber-100 dark:border-amber-800 capitalize">
            {profile.writingStyle}
          </span>
        </div>

        {/* Tone keywords */}
        {profile.toneKeywords.length > 0 && (
          <div className="mb-4">
            <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Tone</p>
            <div className="flex flex-wrap gap-1">
              {profile.toneKeywords.slice(0, 4).map((keyword) => (
                <span
                  key={keyword}
                  className="inline-flex items-center px-2 py-0.5 rounded text-xs text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-800 capitalize"
                >
                  {keyword}
                </span>
              ))}
              {profile.toneKeywords.length > 4 && (
                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs text-gray-400">
                  +{profile.toneKeywords.length - 4}
                </span>
              )}
            </div>
          </div>
        )}

        {/* Target audience preview */}
        {profile.targetAudience && (
          <div className="mb-4">
            <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Target Audience</p>
            <p className="text-sm text-gray-700 dark:text-gray-300 line-clamp-2">
              {profile.targetAudience}
            </p>
          </div>
        )}

        {/* Brand values */}
        {profile.brandValues.length > 0 && (
          <div className="mb-4">
            <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Brand Values</p>
            <div className="flex flex-wrap gap-1">
              {profile.brandValues.slice(0, 3).map((value) => (
                <span
                  key={value}
                  className="inline-flex items-center px-2 py-0.5 rounded text-xs text-amber-600 dark:text-amber-300 bg-amber-50 dark:bg-amber-900/30 border border-amber-100 dark:border-amber-800"
                >
                  {value}
                </span>
              ))}
              {profile.brandValues.length > 3 && (
                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs text-gray-400">
                  +{profile.brandValues.length - 3}
                </span>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="px-5 pb-4 flex items-center gap-2">
        {!profile.isDefault && onSetDefault && (
          <button
            type="button"
            onClick={() => onSetDefault(profile)}
            className="flex-1 inline-flex justify-center items-center gap-1.5 py-2 px-3 text-xs font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2"
          >
            <StarIcon className="w-3.5 h-3.5" />
            Set Default
          </button>
        )}
        {onEdit && (
          <button
            type="button"
            onClick={() => onEdit(profile)}
            className="inline-flex justify-center items-center p-2 text-gray-500 dark:text-gray-400 hover:text-amber-600 dark:hover:text-amber-400 hover:bg-amber-50 dark:hover:bg-amber-900/30 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2"
            title="Edit profile"
          >
            <PencilSquareIcon className="w-4 h-4" />
          </button>
        )}
        {onDelete && (
          <button
            type="button"
            onClick={() => onDelete(profile)}
            className="inline-flex justify-center items-center p-2 text-gray-500 dark:text-gray-400 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/30 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
            title="Delete profile"
          >
            <TrashIcon className="w-4 h-4" />
          </button>
        )}
      </div>
    </motion.div>
  )
}
