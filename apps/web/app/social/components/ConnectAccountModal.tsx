'use client'

import { useState } from 'react'
import { XMarkIcon } from '@heroicons/react/24/outline'
import { API_ENDPOINTS, getDefaultHeaders } from '../../../lib/api'
import type { ToastOptions } from '../../../hooks/useToast'
import type { SocialPlatform } from '../../../types/social'
import { PLATFORM_CONFIG } from '../../../types/social'
import PlatformIcon from './PlatformIcon'

interface ConnectAccountModalProps {
  onClose: () => void
  onConnected: () => void
  showToast: (opts: ToastOptions) => void
}

const PLATFORMS: SocialPlatform[] = ['twitter', 'linkedin', 'facebook', 'instagram']

export default function ConnectAccountModal({ onClose, onConnected, showToast }: ConnectAccountModalProps) {
  const [connecting, setConnecting] = useState<SocialPlatform | null>(null)

  async function handleConnect(platform: SocialPlatform) {
    setConnecting(platform)

    try {
      const headers = await getDefaultHeaders()
      const res = await fetch(API_ENDPOINTS.social.connectAccount(platform), {
        method: 'POST',
        headers,
        body: JSON.stringify({ redirect_uri: `${window.location.origin}/social/callback` }),
      })

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}))
        throw new Error(errData?.detail || errData?.error || `HTTP ${res.status}`)
      }

      const data = await res.json()
      const authUrl = data.authorization_url

      if (!authUrl) throw new Error('No authorization URL returned.')

      // Open OAuth in popup
      const popup = window.open(authUrl, 'social-auth', 'width=600,height=700,scrollbars=yes')

      // Listen for callback message
      const handler = (event: MessageEvent) => {
        if (event.origin !== window.location.origin) return
        if (event.data?.type === 'social-oauth-success') {
          window.removeEventListener('message', handler)
          popup?.close()
          showToast({ message: `${PLATFORM_CONFIG[platform].name} connected!`, variant: 'success' })
          onConnected()
          onClose()
        } else if (event.data?.type === 'social-oauth-error') {
          window.removeEventListener('message', handler)
          popup?.close()
          showToast({ message: event.data.error || 'OAuth failed.', variant: 'error' })
          setConnecting(null)
        }
      }
      window.addEventListener('message', handler)

      // Poll for popup close (fallback)
      const interval = setInterval(() => {
        if (popup?.closed) {
          clearInterval(interval)
          window.removeEventListener('message', handler)
          setConnecting(null)
        }
      }, 1000)
    } catch (err) {
      showToast({ message: err instanceof Error ? err.message : 'Failed to initiate OAuth.', variant: 'error' })
      setConnecting(null)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="fixed inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />
      <div className="relative w-full max-w-md rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-xl p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Connect Account</h2>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
          >
            <XMarkIcon className="w-5 h-5" />
          </button>
        </div>

        <div className="space-y-3">
          {PLATFORMS.map((platform) => {
            const config = PLATFORM_CONFIG[platform]
            const isConnecting = connecting === platform
            return (
              <button
                key={platform}
                type="button"
                onClick={() => handleConnect(platform)}
                disabled={connecting !== null}
                className="w-full flex items-center gap-3 px-4 py-3 rounded-xl border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 transition-colors text-left"
              >
                <PlatformIcon platform={platform} />
                <span className="flex-1 text-sm font-medium text-gray-900 dark:text-gray-100">
                  {config.name}
                </span>
                {isConnecting && (
                  <svg className="animate-spin h-4 w-4 text-gray-400" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                )}
              </button>
            )
          })}
        </div>
      </div>
    </div>
  )
}
