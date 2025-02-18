'use client'

import { useState } from 'react'
import { API_ENDPOINTS, getDefaultHeaders } from '../../../lib/api'
import type { ToastOptions } from '../../../hooks/useToast'
import type { SocialPlatform, RecurrenceType, SocialAccount } from '../../../types/social'
import { PLATFORM_CONFIG } from '../../../types/social'
import PlatformIcon from './PlatformIcon'

interface PostComposerProps {
  accounts: SocialAccount[]
  showToast: (opts: ToastOptions) => void
  onScheduled: () => void
}

const RECURRENCE_OPTIONS: { value: RecurrenceType; label: string }[] = [
  { value: 'none', label: 'One-time' },
  { value: 'daily', label: 'Daily' },
  { value: 'weekly', label: 'Weekly' },
  { value: 'monthly', label: 'Monthly' },
]

export default function PostComposer({ accounts, showToast, onScheduled }: PostComposerProps) {
  const [selectedAccountId, setSelectedAccountId] = useState(accounts[0]?.id || '')
  const [text, setText] = useState('')
  const [mediaUrl, setMediaUrl] = useState('')
  const [scheduledAt, setScheduledAt] = useState('')
  const [recurrence, setRecurrence] = useState<RecurrenceType>('none')
  const [loading, setLoading] = useState(false)
  const [suggestingTime, setSuggestingTime] = useState(false)

  const selectedAccount = accounts.find((a) => a.id === selectedAccountId)
  const platform: SocialPlatform | undefined = selectedAccount?.platform
  const maxChars = platform ? PLATFORM_CONFIG[platform].maxChars : 10000
  const charCount = text.length
  const isOverLimit = charCount > maxChars

  async function handleSuggestTime() {
    if (!platform) return
    setSuggestingTime(true)
    try {
      const headers = await getDefaultHeaders()
      const res = await fetch(`${API_ENDPOINTS.social.suggestTime}?platform=${platform}`, { headers })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      if (data.suggested_time) {
        setScheduledAt(data.suggested_time.slice(0, 16))
        showToast({ message: 'Optimal time suggested!', variant: 'success' })
      }
    } catch {
      showToast({ message: 'Could not suggest optimal time.', variant: 'warning' })
    } finally {
      setSuggestingTime(false)
    }
  }

  async function handleSchedule(e: React.FormEvent) {
    e.preventDefault()
    if (!selectedAccountId || !text.trim() || !scheduledAt) return

    setLoading(true)
    try {
      const headers = await getDefaultHeaders()
      const body: Record<string, unknown> = {
        account_id: selectedAccountId,
        content: { text },
        scheduled_at: new Date(scheduledAt).toISOString(),
        recurrence,
      }

      if (mediaUrl.trim()) {
        body.content = { text, media: [{ url: mediaUrl.trim(), type: 'image' }] }
      }

      const res = await fetch(API_ENDPOINTS.social.schedulePost, {
        method: 'POST',
        headers,
        body: JSON.stringify(body),
      })

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}))
        throw new Error(errData?.detail || errData?.error || `HTTP ${res.status}`)
      }

      showToast({ message: 'Post scheduled!', variant: 'success' })
      setText('')
      setMediaUrl('')
      setScheduledAt('')
      setRecurrence('none')
      onScheduled()
    } catch (err) {
      showToast({ message: err instanceof Error ? err.message : 'Failed to schedule post.', variant: 'error' })
    } finally {
      setLoading(false)
    }
  }

  if (accounts.length === 0) {
    return (
      <div className="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-6 text-center">
        <p className="text-sm text-gray-500 dark:text-gray-400">Connect an account to start scheduling posts.</p>
      </div>
    )
  }

  return (
    <form onSubmit={handleSchedule} className="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-5 space-y-4">
      <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">New Post</h3>

      {/* Account selector */}
      <div className="flex items-center gap-3">
        <select
          value={selectedAccountId}
          onChange={(e) => setSelectedAccountId(e.target.value)}
          className="flex-1 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:border-amber-500 focus:ring-1 focus:ring-amber-500"
        >
          {accounts.map((a) => (
            <option key={a.id} value={a.id}>
              {PLATFORM_CONFIG[a.platform].name} — @{a.username}
            </option>
          ))}
        </select>
        {platform && <PlatformIcon platform={platform} size="sm" />}
      </div>

      {/* Content */}
      <div>
        <textarea
          rows={4}
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="What do you want to share?"
          className="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-4 py-3 text-sm text-gray-900 dark:text-gray-100 placeholder-gray-400 focus:border-amber-500 focus:ring-1 focus:ring-amber-500"
          required
        />
        <div className="flex justify-between mt-1 text-xs">
          {platform && (
            <span className={`font-medium ${isOverLimit ? 'text-red-600' : 'text-gray-400'}`}>
              {charCount}/{maxChars}
            </span>
          )}
        </div>
      </div>

      {/* Media URL */}
      <input
        type="url"
        value={mediaUrl}
        onChange={(e) => setMediaUrl(e.target.value)}
        placeholder="Media URL (optional)"
        className="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-4 py-2.5 text-sm text-gray-900 dark:text-gray-100 placeholder-gray-400 focus:border-amber-500 focus:ring-1 focus:ring-amber-500"
      />

      {/* Schedule + recurrence */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="sm:col-span-2">
          <label htmlFor="schedule-at" className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Schedule for</label>
          <div className="flex gap-2">
            <input
              id="schedule-at"
              type="datetime-local"
              value={scheduledAt}
              onChange={(e) => setScheduledAt(e.target.value)}
              className="flex-1 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:border-amber-500 focus:ring-1 focus:ring-amber-500"
              required
            />
            <button
              type="button"
              onClick={handleSuggestTime}
              disabled={suggestingTime || !platform}
              className="px-3 py-2 rounded-lg text-xs font-medium border border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50 transition-colors whitespace-nowrap"
            >
              {suggestingTime ? 'Suggesting...' : 'Optimal Time'}
            </button>
          </div>
        </div>
        <div>
          <label htmlFor="recurrence" className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Recurrence</label>
          <select
            id="recurrence"
            value={recurrence}
            onChange={(e) => setRecurrence(e.target.value as RecurrenceType)}
            className="w-full rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:border-amber-500 focus:ring-1 focus:ring-amber-500"
          >
            {RECURRENCE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>
      </div>

      <button
        type="submit"
        disabled={loading || !text.trim() || !scheduledAt || isOverLimit}
        className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-medium bg-amber-600 text-white hover:bg-amber-700 disabled:bg-gray-300 dark:disabled:bg-gray-700 disabled:cursor-not-allowed transition-colors"
      >
        {loading ? 'Scheduling...' : 'Schedule Post'}
      </button>
    </form>
  )
}
