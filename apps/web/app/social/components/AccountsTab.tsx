'use client'

import { useState, useEffect, useCallback } from 'react'
import { PlusIcon, UserGroupIcon } from '@heroicons/react/24/outline'
import { API_ENDPOINTS, getDefaultHeaders } from '../../../lib/api'
import type { ToastOptions } from '../../../hooks/useToast'
import type { ConfirmOptions } from '../../../hooks/useConfirmModal'
import type { SocialAccount } from '../../../types/social'
import { PLATFORM_CONFIG } from '../../../types/social'
import AccountCard from './AccountCard'
import ConnectAccountModal from './ConnectAccountModal'

interface AccountsTabProps {
  showToast: (opts: ToastOptions) => void
  confirm: (opts: ConfirmOptions) => Promise<boolean>
}

export default function AccountsTab({ showToast, confirm }: AccountsTabProps) {
  const [accounts, setAccounts] = useState<SocialAccount[]>([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)

  const fetchAccounts = useCallback(async () => {
    try {
      const headers = await getDefaultHeaders()
      const res = await fetch(API_ENDPOINTS.social.accounts, { headers })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setAccounts(Array.isArray(data) ? data : data.accounts || [])
    } catch {
      showToast({ message: 'Failed to load accounts.', variant: 'error' })
    } finally {
      setLoading(false)
    }
  }, [showToast])

  useEffect(() => {
    fetchAccounts()
  }, [fetchAccounts])

  async function handleDisconnect(accountId: string) {
    const account = accounts.find((a) => a.id === accountId)
    const platformName = account ? PLATFORM_CONFIG[account.platform].name : 'this account'

    const confirmed = await confirm({
      title: `Disconnect ${platformName}?`,
      message: 'Scheduled posts for this account will be cancelled.',
      variant: 'danger',
      confirmLabel: 'Disconnect',
    })
    if (!confirmed) return

    try {
      const headers = await getDefaultHeaders()
      const res = await fetch(API_ENDPOINTS.social.disconnectAccount(accountId), { method: 'DELETE', headers })
      if (!res.ok && res.status !== 204) throw new Error(`HTTP ${res.status}`)
      setAccounts((prev) => prev.filter((a) => a.id !== accountId))
      showToast({ message: 'Account disconnected.', variant: 'success' })
    } catch {
      showToast({ message: 'Failed to disconnect account.', variant: 'error' })
    }
  }

  if (loading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {[1, 2].map((n) => (
          <div key={n} className="rounded-xl border border-gray-200 dark:border-gray-700 p-5 animate-pulse">
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2 mb-2" />
            <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/3" />
          </div>
        ))}
      </div>
    )
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-sm font-semibold text-gray-900 dark:text-gray-100">Connected Accounts</h2>
        <button
          type="button"
          onClick={() => setShowModal(true)}
          className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium bg-amber-600 text-white hover:bg-amber-700 transition-colors"
        >
          <PlusIcon className="w-4 h-4" />
          Connect Account
        </button>
      </div>

      {accounts.length === 0 ? (
        <div className="text-center py-16">
          <UserGroupIcon className="w-12 h-12 mx-auto text-gray-300 dark:text-gray-600 mb-4" />
          <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-1">No accounts connected</h3>
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
            Connect your social media accounts to start scheduling posts.
          </p>
          <button
            type="button"
            onClick={() => setShowModal(true)}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium bg-amber-600 text-white hover:bg-amber-700 transition-colors"
          >
            <PlusIcon className="w-4 h-4" />
            Connect Account
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {accounts.map((account) => (
            <AccountCard key={account.id} account={account} onDisconnect={handleDisconnect} />
          ))}
        </div>
      )}

      {showModal && (
        <ConnectAccountModal
          onClose={() => setShowModal(false)}
          onConnected={fetchAccounts}
          showToast={showToast}
        />
      )}
    </div>
  )
}
