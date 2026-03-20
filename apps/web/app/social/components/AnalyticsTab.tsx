'use client'

import { useState, useEffect } from 'react'
import { ChartBarIcon } from '@heroicons/react/24/outline'
import { API_ENDPOINTS, getDefaultHeaders } from '../../../lib/api'
import type { Campaign, CampaignAnalytics } from '../../../types/social'
import PlatformIcon from './PlatformIcon'

export default function AnalyticsTab() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([])
  const [selectedCampaignId, setSelectedCampaignId] = useState<string | null>(null)
  const [analytics, setAnalytics] = useState<CampaignAnalytics | null>(null)
  const [loading, setLoading] = useState(true)
  const [analyticsLoading, setAnalyticsLoading] = useState(false)

  useEffect(() => {
    fetchCampaigns()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function fetchCampaigns() {
    try {
      const headers = await getDefaultHeaders()
      const res = await fetch(API_ENDPOINTS.social.campaigns, { headers })
      if (res.ok) {
        const data = await res.json()
        const list: Campaign[] = Array.isArray(data) ? data : data.campaigns || []
        setCampaigns(list)
        const first = list[0]
        if (first) {
          setSelectedCampaignId(first.id)
          fetchAnalytics(first.id)
        }
      }
    } catch {
      // Non-critical
    } finally {
      setLoading(false)
    }
  }

  async function fetchAnalytics(campaignId: string) {
    setAnalyticsLoading(true)
    try {
      const headers = await getDefaultHeaders()
      const res = await fetch(API_ENDPOINTS.social.campaignAnalytics(campaignId), { headers })
      if (res.ok) {
        const data: CampaignAnalytics = await res.json()
        setAnalytics(data)
      } else {
        setAnalytics(null)
      }
    } catch {
      setAnalytics(null)
    } finally {
      setAnalyticsLoading(false)
    }
  }

  function handleSelectCampaign(id: string) {
    setSelectedCampaignId(id)
    fetchAnalytics(id)
  }

  if (loading) {
    return (
      <div className="animate-pulse space-y-4">
        <div className="h-10 bg-gray-200 dark:bg-gray-700 rounded w-1/3" />
        <div className="grid grid-cols-2 gap-4">
          {[1, 2, 3, 4].map((n) => (
            <div key={n} className="h-24 bg-gray-200 dark:bg-gray-700 rounded-xl" />
          ))}
        </div>
      </div>
    )
  }

  if (campaigns.length === 0) {
    return (
      <div className="text-center py-16">
        <ChartBarIcon className="w-12 h-12 mx-auto text-gray-300 dark:text-gray-600 mb-4" />
        <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-1">No analytics data</h3>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Create and run campaigns to see performance analytics.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Campaign selector */}
      <div>
        <label htmlFor="analytics-campaign" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
          Campaign
        </label>
        <select
          id="analytics-campaign"
          value={selectedCampaignId || ''}
          onChange={(e) => handleSelectCampaign(e.target.value)}
          className="w-full sm:w-auto rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 px-4 py-2.5 text-sm text-gray-900 dark:text-gray-100 focus:border-amber-500 focus:ring-1 focus:ring-amber-500"
        >
          {campaigns.map((c) => (
            <option key={c.id} value={c.id}>{c.name}</option>
          ))}
        </select>
      </div>

      {analyticsLoading ? (
        <div className="animate-pulse grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((n) => (
            <div key={n} className="h-24 bg-gray-200 dark:bg-gray-700 rounded-xl" />
          ))}
        </div>
      ) : analytics ? (
        <div className="space-y-6">
          {/* Overview stats */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <StatCard label="Total Posts" value={analytics.total_posts} />
            <StatCard label="Published" value={analytics.published_posts} />
            <StatCard label="Failed" value={analytics.failed_posts} variant="red" />
            <StatCard
              label="Success Rate"
              value={analytics.total_posts > 0
                ? `${Math.round((analytics.published_posts / analytics.total_posts) * 100)}%`
                : 'N/A'}
            />
          </div>

          {/* Per-platform stats */}
          {analytics.stats.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-4">Platform Breakdown</h3>
              <div className="space-y-4">
                {analytics.stats.map((stat) => (
                  <div
                    key={stat.platform}
                    className="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-4"
                  >
                    <div className="flex items-center gap-2 mb-3">
                      <PlatformIcon platform={stat.platform} size="sm" />
                      <span className="text-sm font-medium text-gray-900 dark:text-gray-100 capitalize">{stat.platform}</span>
                    </div>
                    <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                      <MiniStat label="Impressions" value={stat.impressions.toLocaleString()} />
                      <MiniStat label="Reach" value={stat.reach.toLocaleString()} />
                      <MiniStat label="Engagements" value={stat.engagements.toLocaleString()} />
                      <MiniStat label="Clicks" value={stat.clicks.toLocaleString()} />
                      <MiniStat label="Engagement Rate" value={`${stat.engagement_rate.toFixed(1)}%`} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="text-center py-12">
          <p className="text-sm text-gray-500 dark:text-gray-400">No analytics available for this campaign yet.</p>
        </div>
      )}
    </div>
  )
}

function StatCard({ label, value, variant }: { label: string; value: string | number; variant?: 'red' }) {
  return (
    <div className="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-4">
      <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">{label}</p>
      <p className={`text-2xl font-semibold ${
        variant === 'red' ? 'text-red-600 dark:text-red-400' : 'text-gray-900 dark:text-gray-100'
      }`}>
        {value}
      </p>
    </div>
  )
}

function MiniStat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs text-gray-500 dark:text-gray-400">{label}</p>
      <p className="text-sm font-semibold text-gray-900 dark:text-gray-100">{value}</p>
    </div>
  )
}
