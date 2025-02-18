'use client'

import { useState, useEffect, useCallback } from 'react'
import { CalendarIcon } from '@heroicons/react/24/outline'
import { API_ENDPOINTS, getDefaultHeaders } from '../../../lib/api'
import type { ToastOptions } from '../../../hooks/useToast'
import type { SocialAccount, ScheduledPost } from '../../../types/social'
import PostComposer from './PostComposer'
import ScheduledPostCard from './ScheduledPostCard'

interface ScheduleTabProps {
  showToast: (opts: ToastOptions) => void
}

export default function ScheduleTab({ showToast }: ScheduleTabProps) {
  const [accounts, setAccounts] = useState<SocialAccount[]>([])
  const [posts, setPosts] = useState<ScheduledPost[]>([])
  const [loading, setLoading] = useState(true)

  const fetchData = useCallback(async () => {
    try {
      const headers = await getDefaultHeaders()
      const [accountsRes, postsRes] = await Promise.all([
        fetch(API_ENDPOINTS.social.accounts, { headers }),
        fetch(API_ENDPOINTS.social.scheduledPosts, { headers }),
      ])

      if (accountsRes.ok) {
        const data = await accountsRes.json()
        setAccounts(Array.isArray(data) ? data : data.accounts || [])
      }
      if (postsRes.ok) {
        const data = await postsRes.json()
        setPosts(Array.isArray(data) ? data : data.posts || [])
      }
    } catch {
      showToast({ message: 'Failed to load schedule data.', variant: 'error' })
    } finally {
      setLoading(false)
    }
  }, [showToast])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  async function handleCancelPost(postId: string) {
    try {
      const headers = await getDefaultHeaders()
      const res = await fetch(API_ENDPOINTS.social.cancelPost(postId), { method: 'DELETE', headers })
      if (!res.ok && res.status !== 204) throw new Error(`HTTP ${res.status}`)
      setPosts((prev) => prev.map((p) => (p.id === postId ? { ...p, status: 'cancelled' as const } : p)))
      showToast({ message: 'Post cancelled.', variant: 'success' })
    } catch {
      showToast({ message: 'Failed to cancel post.', variant: 'error' })
    }
  }

  if (loading) {
    return (
      <div className="space-y-4 animate-pulse">
        <div className="rounded-xl border border-gray-200 dark:border-gray-700 p-6">
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/3 mb-4" />
          <div className="h-20 bg-gray-200 dark:bg-gray-700 rounded" />
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <PostComposer accounts={accounts} showToast={showToast} onScheduled={fetchData} />

      <div>
        <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-4">Scheduled Posts</h3>
        {posts.length === 0 ? (
          <div className="text-center py-12">
            <CalendarIcon className="w-10 h-10 mx-auto text-gray-300 dark:text-gray-600 mb-3" />
            <p className="text-sm text-gray-500 dark:text-gray-400">No scheduled posts yet.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {posts.map((post) => (
              <ScheduledPostCard key={post.id} post={post} onCancel={handleCancelPost} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
