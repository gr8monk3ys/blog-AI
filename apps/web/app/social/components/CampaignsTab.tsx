'use client'

import { useState, useEffect, useCallback } from 'react'
import { PlusIcon, RocketLaunchIcon } from '@heroicons/react/24/outline'
import { AnimatePresence, motion } from 'framer-motion'
import { API_ENDPOINTS, getDefaultHeaders } from '../../../lib/api'
import type { ToastOptions } from '../../../hooks/useToast'
import type { ConfirmOptions } from '../../../hooks/useConfirmModal'
import type { Campaign, SocialAccount } from '../../../types/social'
import CampaignCard from './CampaignCard'
import CreateCampaignForm from './CreateCampaignForm'

interface CampaignsTabProps {
  showToast: (opts: ToastOptions) => void
  confirm: (opts: ConfirmOptions) => Promise<boolean>
}

export default function CampaignsTab({ showToast, confirm }: CampaignsTabProps) {
  const [campaigns, setCampaigns] = useState<Campaign[]>([])
  const [accounts, setAccounts] = useState<SocialAccount[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)

  const fetchData = useCallback(async () => {
    try {
      const headers = await getDefaultHeaders()
      const [campaignsRes, accountsRes] = await Promise.all([
        fetch(API_ENDPOINTS.social.campaigns, { headers }),
        fetch(API_ENDPOINTS.social.accounts, { headers }),
      ])

      if (campaignsRes.ok) {
        const data = await campaignsRes.json()
        setCampaigns(Array.isArray(data) ? data : data.campaigns || [])
      }
      if (accountsRes.ok) {
        const data = await accountsRes.json()
        setAccounts(Array.isArray(data) ? data : data.accounts || [])
      }
    } catch {
      showToast({ message: 'Failed to load campaigns.', variant: 'error' })
    } finally {
      setLoading(false)
    }
  }, [showToast])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  async function handlePause(id: string) {
    try {
      const headers = await getDefaultHeaders()
      const res = await fetch(API_ENDPOINTS.social.pauseCampaign(id), { method: 'POST', headers })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      setCampaigns((prev) => prev.map((c) => (c.id === id ? { ...c, status: 'paused' as const } : c)))
      showToast({ message: 'Campaign paused.', variant: 'success' })
    } catch {
      showToast({ message: 'Failed to pause campaign.', variant: 'error' })
    }
  }

  async function handleResume(id: string) {
    try {
      const headers = await getDefaultHeaders()
      const res = await fetch(API_ENDPOINTS.social.resumeCampaign(id), { method: 'POST', headers })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      setCampaigns((prev) => prev.map((c) => (c.id === id ? { ...c, status: 'active' as const } : c)))
      showToast({ message: 'Campaign resumed.', variant: 'success' })
    } catch {
      showToast({ message: 'Failed to resume campaign.', variant: 'error' })
    }
  }

  async function handleCancel(id: string) {
    const confirmed = await confirm({
      title: 'Cancel campaign?',
      message: 'All scheduled posts in this campaign will be cancelled.',
      variant: 'danger',
      confirmLabel: 'Cancel Campaign',
    })
    if (!confirmed) return

    try {
      const headers = await getDefaultHeaders()
      const res = await fetch(API_ENDPOINTS.social.cancelCampaign(id), { method: 'DELETE', headers })
      if (!res.ok && res.status !== 204) throw new Error(`HTTP ${res.status}`)
      setCampaigns((prev) => prev.map((c) => (c.id === id ? { ...c, status: 'cancelled' as const } : c)))
      showToast({ message: 'Campaign cancelled.', variant: 'success' })
    } catch {
      showToast({ message: 'Failed to cancel campaign.', variant: 'error' })
    }
  }

  if (loading) {
    return (
      <div className="space-y-4 animate-pulse">
        {[1, 2].map((n) => (
          <div key={n} className="rounded-xl border border-gray-200 dark:border-gray-700 p-5">
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/3 mb-2" />
            <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/2" />
          </div>
        ))}
      </div>
    )
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-sm font-semibold text-gray-900 dark:text-gray-100">Campaigns</h2>
        {!showForm && (
          <button
            type="button"
            onClick={() => setShowForm(true)}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium bg-amber-600 text-white hover:bg-amber-700 transition-colors"
          >
            <PlusIcon className="w-4 h-4" />
            New Campaign
          </button>
        )}
      </div>

      <AnimatePresence mode="wait">
        {showForm && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
            className="mb-6 overflow-hidden"
          >
            <CreateCampaignForm
              accounts={accounts}
              onClose={() => setShowForm(false)}
              onSuccess={() => { setShowForm(false); fetchData() }}
              showToast={showToast}
            />
          </motion.div>
        )}
      </AnimatePresence>

      {campaigns.length === 0 ? (
        <div className="text-center py-16">
          <RocketLaunchIcon className="w-12 h-12 mx-auto text-gray-300 dark:text-gray-600 mb-4" />
          <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-1">No campaigns yet</h3>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Create a campaign to schedule content across multiple platforms.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {campaigns.map((campaign) => (
            <CampaignCard
              key={campaign.id}
              campaign={campaign}
              onPause={handlePause}
              onResume={handleResume}
              onCancel={handleCancel}
            />
          ))}
        </div>
      )}
    </div>
  )
}
