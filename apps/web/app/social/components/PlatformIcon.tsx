'use client'

import type { SocialPlatform } from '../../../types/social'
import { PLATFORM_CONFIG } from '../../../types/social'

interface PlatformIconProps {
  platform: SocialPlatform
  size?: 'sm' | 'md'
}

export default function PlatformIcon({ platform, size = 'md' }: PlatformIconProps) {
  const config = PLATFORM_CONFIG[platform]
  const sizeClasses = size === 'sm' ? 'w-6 h-6 text-xs' : 'w-8 h-8 text-sm'

  return (
    <div
      className={`inline-flex items-center justify-center rounded-lg font-bold ${sizeClasses} ${config.bgColor} ${config.color}`}
      title={config.name}
    >
      {config.icon}
    </div>
  )
}
