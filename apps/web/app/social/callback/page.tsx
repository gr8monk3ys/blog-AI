'use client'

import { useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { API_ENDPOINTS, getDefaultHeaders } from '../../../lib/api'

export default function SocialCallbackPage() {
  const searchParams = useSearchParams()
  const [status, setStatus] = useState<'processing' | 'success' | 'error'>('processing')
  const [errorMessage, setErrorMessage] = useState('')

  useEffect(() => {
    handleCallback()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function handleCallback() {
    const code = searchParams.get('code')
    const state = searchParams.get('state')
    const error = searchParams.get('error')

    if (error) {
      setStatus('error')
      setErrorMessage(searchParams.get('error_description') || error)
      notifyParent('error', error)
      return
    }

    if (!code || !state) {
      setStatus('error')
      setErrorMessage('Missing authorization code or state parameter.')
      notifyParent('error', 'Missing parameters')
      return
    }

    // Extract platform from state (format: platform:random-state)
    const platform = state.split(':')[0]
    if (!platform) {
      setStatus('error')
      setErrorMessage('Invalid state parameter.')
      notifyParent('error', 'Invalid state')
      return
    }

    try {
      const headers = await getDefaultHeaders()
      const url = `${API_ENDPOINTS.social.oauthCallback(platform)}?code=${encodeURIComponent(code)}&state=${encodeURIComponent(state)}`
      const res = await fetch(url, { headers })

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}))
        throw new Error(errData?.detail || errData?.error || `HTTP ${res.status}`)
      }

      setStatus('success')
      notifyParent('success')

      // Auto-close after a brief delay
      setTimeout(() => {
        window.close()
      }, 1500)
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'OAuth callback failed.'
      setStatus('error')
      setErrorMessage(msg)
      notifyParent('error', msg)
    }
  }

  function notifyParent(type: 'success' | 'error', error?: string) {
    if (window.opener) {
      window.opener.postMessage(
        { type: type === 'success' ? 'social-oauth-success' : 'social-oauth-error', error },
        window.location.origin
      )
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="text-center">
        {status === 'processing' && (
          <>
            <svg className="animate-spin h-8 w-8 mx-auto text-amber-600 mb-4" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            <p className="text-sm text-gray-600 dark:text-gray-400">Connecting your account...</p>
          </>
        )}
        {status === 'success' && (
          <>
            <div className="w-12 h-12 mx-auto mb-4 rounded-full bg-emerald-100 dark:bg-emerald-900/40 flex items-center justify-center">
              <svg className="w-6 h-6 text-emerald-600 dark:text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <p className="text-sm font-medium text-gray-900 dark:text-gray-100">Account connected!</p>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">This window will close automatically.</p>
          </>
        )}
        {status === 'error' && (
          <>
            <div className="w-12 h-12 mx-auto mb-4 rounded-full bg-red-100 dark:bg-red-900/40 flex items-center justify-center">
              <svg className="w-6 h-6 text-red-600 dark:text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <p className="text-sm font-medium text-gray-900 dark:text-gray-100">Connection failed</p>
            <p className="text-xs text-red-600 dark:text-red-400 mt-1 max-w-xs">{errorMessage}</p>
            <button
              type="button"
              onClick={() => window.close()}
              className="mt-4 px-4 py-2 rounded-lg text-sm font-medium bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700"
            >
              Close
            </button>
          </>
        )}
      </div>
    </div>
  )
}
