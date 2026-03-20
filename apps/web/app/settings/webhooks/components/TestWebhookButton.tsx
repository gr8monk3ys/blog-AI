'use client'

import { useState } from 'react'
import { API_ENDPOINTS, getDefaultHeaders } from '../../../../lib/api'
import type { ToastOptions } from '../../../../hooks/useToast'
import type { WebhookTestResponse } from '../../../../types/webhooks'

interface TestWebhookButtonProps {
  subscriptionId: string
  showToast: (opts: ToastOptions) => void
}

export default function TestWebhookButton({ subscriptionId, showToast }: TestWebhookButtonProps) {
  const [testing, setTesting] = useState(false)
  const [result, setResult] = useState<WebhookTestResponse | null>(null)

  async function handleTest() {
    setTesting(true)
    setResult(null)

    try {
      const headers = await getDefaultHeaders()
      const res = await fetch(API_ENDPOINTS.webhooks.test, {
        method: 'POST',
        headers,
        body: JSON.stringify({ subscription_id: subscriptionId, event_type: 'test' }),
      })

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}))
        throw new Error(errData?.detail || errData?.error || `HTTP ${res.status}`)
      }

      const data: WebhookTestResponse = await res.json()
      setResult(data)

      if (data.success) {
        showToast({ message: `Test delivered (${data.status_code}, ${data.response_time_ms}ms)`, variant: 'success' })
      } else {
        showToast({ message: data.error || 'Test delivery failed.', variant: 'error' })
      }
    } catch (err) {
      showToast({ message: err instanceof Error ? err.message : 'Test failed.', variant: 'error' })
    } finally {
      setTesting(false)
    }
  }

  return (
    <div className="inline-flex items-center gap-2">
      <button
        type="button"
        onClick={handleTest}
        disabled={testing}
        className="px-3 py-1.5 rounded-lg text-xs font-medium border border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50 transition-colors"
      >
        {testing ? 'Testing...' : 'Test'}
      </button>
      {result && (
        <span className={`text-xs font-medium ${result.success ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'}`}>
          {result.success ? `${result.status_code} (${result.response_time_ms}ms)` : result.error || 'Failed'}
        </span>
      )}
    </div>
  )
}
