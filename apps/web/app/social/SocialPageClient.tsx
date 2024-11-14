'use client'

import { useState } from 'react'
import { ChatBubbleLeftRightIcon } from '@heroicons/react/24/outline'
import { useToast } from '../../hooks/useToast'
import { useConfirmModal } from '../../hooks/useConfirmModal'
import AccountsTab from './components/AccountsTab'
import ScheduleTab from './components/ScheduleTab'
import CampaignsTab from './components/CampaignsTab'
import AnalyticsTab from './components/AnalyticsTab'

const TABS = [
  { id: 'accounts', label: 'Accounts' },
  { id: 'schedule', label: 'Schedule' },
  { id: 'campaigns', label: 'Campaigns' },
  { id: 'analytics', label: 'Analytics' },
] as const

type TabId = (typeof TABS)[number]['id']

export default function SocialPageClient() {
  const [activeTab, setActiveTab] = useState<TabId>('accounts')
  const { showToast, ToastComponent } = useToast()
  const { confirm, ConfirmModalComponent } = useConfirmModal()

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <div className="flex items-center gap-3 mb-8">
        <div className="inline-flex items-center justify-center w-11 h-11 rounded-xl bg-amber-100/80 dark:bg-amber-900/40 text-amber-700">
          <ChatBubbleLeftRightIcon className="w-5 h-5" aria-hidden="true" />
        </div>
        <div>
          <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">Social Media</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">Schedule posts, run campaigns, and track performance</p>
        </div>
      </div>

      {/* Tab bar */}
      <div className="border-b border-gray-200 dark:border-gray-700 mb-6">
        <nav className="flex gap-6" aria-label="Social media tabs">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              className={`pb-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-amber-600 text-amber-600'
                  : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {activeTab === 'accounts' && <AccountsTab showToast={showToast} confirm={confirm} />}
      {activeTab === 'schedule' && <ScheduleTab showToast={showToast} />}
      {activeTab === 'campaigns' && <CampaignsTab showToast={showToast} confirm={confirm} />}
      {activeTab === 'analytics' && <AnalyticsTab />}

      <ToastComponent />
      <ConfirmModalComponent />
    </div>
  )
}
