'use client'

import { useState, useEffect } from 'react'
import { m, AnimatePresence } from 'framer-motion'
import SiteHeader from '../../components/SiteHeader'
import SiteFooter from '../../components/SiteFooter'
import BrandProfileCard from '../../components/brand/BrandProfileCard'
import BrandProfileForm, { BrandProfileFormData } from '../../components/brand/BrandProfileForm'
import {
  SparklesIcon,
  PlusIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline'
import { BrandProfile, SAMPLE_BRAND_PROFILES } from '../../types/brand'
import { useConfirmModal } from '../../hooks/useConfirmModal'
import { getDefaultHeaders } from '../../lib/api'

async function loadBrandProfiles(): Promise<BrandProfile[]> {
  try {
    const response = await fetch('/api/brand-profiles', {
      headers: await getDefaultHeaders(),
    })
    const data = await response.json()
    if (data.success && Array.isArray(data.data)) {
      return data.data
    }
  } catch (error) {
    console.error('Error fetching brand profiles:', error)
  }

  return SAMPLE_BRAND_PROFILES
}

function useBrandPageView() {
  const { confirm, ConfirmModalComponent } = useConfirmModal()

  const [profiles, setProfiles] = useState<BrandProfile[]>(SAMPLE_BRAND_PROFILES)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [showForm, setShowForm] = useState(false)
  const [editingProfile, setEditingProfile] = useState<BrandProfile | null>(null)
  const [error, setError] = useState<string | null>(null)

  // Fetch profiles from API
  useEffect(() => {
    let mounted = true

    const initializeProfiles = async () => {
      const loadedProfiles = await loadBrandProfiles()
      if (mounted) {
        setProfiles(loadedProfiles)
        setLoading(false)
      }
    }

    initializeProfiles()

    return () => {
      mounted = false
    }
  }, [])

  const handleCreateProfile = async (data: BrandProfileFormData) => {
    setSaving(true)
    setError(null)

    try {
      const response = await fetch('/api/brand-profiles', {
        method: 'POST',
        headers: await getDefaultHeaders(),
        body: JSON.stringify(data),
      })

      const result = await response.json()

      if (!result.success) {
        throw new Error(result.error || 'Failed to create profile')
      }

      setProfiles((prev) => [result.data, ...prev])
      setShowForm(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create profile')
      throw err
    } finally {
      setSaving(false)
    }
  }

  const handleUpdateProfile = async (data: BrandProfileFormData) => {
    if (!editingProfile) return

    setSaving(true)
    setError(null)

    try {
      const response = await fetch(`/api/brand-profiles/${editingProfile.id}`, {
        method: 'PATCH',
        headers: await getDefaultHeaders(),
        body: JSON.stringify(data),
      })

      const result = await response.json()

      if (!result.success) {
        throw new Error(result.error || 'Failed to update profile')
      }

      setProfiles((prev) =>
        prev.map((p) => (p.id === editingProfile.id ? result.data : p))
      )
      setEditingProfile(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update profile')
      throw err
    } finally {
      setSaving(false)
    }
  }

  const handleDeleteProfile = async (profile: BrandProfile) => {
    const confirmed = await confirm({
      title: 'Delete Brand Profile',
      message: `Are you sure you want to delete "${profile.name}"? This action cannot be undone.`,
      confirmLabel: 'Delete',
      cancelLabel: 'Cancel',
      variant: 'danger',
    })

    if (!confirmed) {
      return
    }

    try {
      const response = await fetch(`/api/brand-profiles/${profile.id}`, {
        method: 'DELETE',
        headers: await getDefaultHeaders(),
      })

      const result = await response.json()

      if (!result.success) {
        throw new Error(result.error || 'Failed to delete profile')
      }

      setProfiles((prev) => prev.filter((p) => p.id !== profile.id))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete profile')
    }
  }

  const handleSetDefault = async (profile: BrandProfile) => {
    try {
      const response = await fetch(`/api/brand-profiles/${profile.id}/default`, {
        method: 'POST',
        headers: await getDefaultHeaders(),
        body: JSON.stringify({}),
      })

      const result = await response.json()

      if (!result.success) {
        throw new Error(result.error || 'Failed to set default profile')
      }

      setProfiles((prev) =>
        prev.map((p) => ({
          ...p,
          isDefault: p.id === profile.id,
        }))
      )
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to set default profile')
    }
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-950 dark:to-gray-900">
      {/* Confirm Modal */}
      <ConfirmModalComponent />

      <SiteHeader />

      {/* Hero Section */}
      <section className="bg-gradient-to-r from-amber-600 to-amber-700 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-16">
          <m.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="text-center"
          >
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-white/10 mb-6">
              <SparklesIcon className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-4">
              Brand Voice Profiles
            </h1>
            <p className="text-lg sm:text-xl text-amber-100 max-w-2xl mx-auto">
              Define your brand&apos;s unique voice and style. Create profiles that ensure
              consistent messaging across all your AI-generated content.
            </p>
          </m.div>
        </div>
      </section>

      {/* Main Content */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
        {/* Error message */}
        {error && (
          <m.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-6 p-4 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 border border-red-100 dark:border-red-800 flex items-center justify-between"
          >
            <span>{error}</span>
            <button
              type="button"
              onClick={() => setError(null)}
              className="text-red-400 hover:text-red-600 dark:hover:text-red-300"
            >
              <XMarkIcon className="w-5 h-5" />
            </button>
          </m.div>
        )}

        {/* Actions */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Your Brand Profiles
            </h2>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {profiles.length} profile{profiles.length !== 1 ? 's' : ''} created
            </p>
          </div>
          {!showForm && !editingProfile && (
            <button
              type="button"
              onClick={() => setShowForm(true)}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-amber-600 rounded-lg hover:bg-amber-700 transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2"
            >
              <PlusIcon className="w-4 h-4" />
              Create Profile
            </button>
          )}
        </div>

        {/* Form */}
        <AnimatePresence mode="wait">
          {(showForm || editingProfile) && (
            <m.div
              key="form"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="mb-8"
            >
              <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-800 p-6">
                <div className="flex items-center justify-between mb-6">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                    {editingProfile ? 'Edit Profile' : 'Create New Profile'}
                  </h3>
                  <button
                    type="button"
                    onClick={() => {
                      setShowForm(false)
                      setEditingProfile(null)
                    }}
                    className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                  >
                    <XMarkIcon className="w-5 h-5" />
                  </button>
                </div>
                <BrandProfileForm
                  key={editingProfile?.id ?? 'new-profile'}
                  profile={editingProfile}
                  onSubmit={editingProfile ? handleUpdateProfile : handleCreateProfile}
                  onCancel={() => {
                    setShowForm(false)
                    setEditingProfile(null)
                  }}
                  isLoading={saving}
                />
              </div>
            </m.div>
          )}
        </AnimatePresence>

        {/* Profiles Grid */}
        <AnimatePresence mode="wait">
          {loading ? (
            <m.div
              key="loading"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4"
            >
              {[1, 2, 3].map((slot) => (
                <div
                  key={`brand-skeleton-${slot}`}
                  className="h-64 bg-gray-100 dark:bg-gray-800 rounded-xl animate-pulse"
                />
              ))}
            </m.div>
          ) : profiles.length === 0 ? (
            <m.div
              key="empty"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="text-center py-12 bg-gray-50 dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800"
            >
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
                <SparklesIcon className="w-8 h-8 text-gray-400" />
              </div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
                No brand profiles yet
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400 max-w-sm mx-auto mb-6">
                Create your first brand voice profile to ensure consistent
                messaging in your AI-generated content.
              </p>
              <button
                type="button"
                onClick={() => setShowForm(true)}
                className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-amber-600 rounded-lg hover:bg-amber-700 transition-colors"
              >
                <PlusIcon className="w-4 h-4" />
                Create Your First Profile
              </button>
            </m.div>
          ) : (
            <m.div
              key="grid"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4"
            >
              {profiles.map((profile, index) => (
                <BrandProfileCard
                  key={profile.id}
                  profile={profile}
                  index={index}
                  onEdit={(p) => setEditingProfile(p)}
                  onDelete={handleDeleteProfile}
                  onSetDefault={handleSetDefault}
                />
              ))}
            </m.div>
          )}
        </AnimatePresence>
      </section>

      {/* Tips Section */}
      <section className="bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-16">
          <m.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.4 }}
          >
            <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-6 text-center">
              Tips for Creating Effective Brand Profiles
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-gray-50 dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
                <div className="w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center mb-4">
                  <span className="text-lg font-bold text-amber-600">1</span>
                </div>
                <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">
                  Be Specific with Tone
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Choose 3-5 tone keywords that truly represent your brand. Avoid
                  generic terms and be as specific as possible.
                </p>
              </div>
              <div className="bg-gray-50 dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
                <div className="w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center mb-4">
                  <span className="text-lg font-bold text-amber-600">2</span>
                </div>
                <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">
                  Provide Example Content
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Include a paragraph of your best content as an example. This helps
                  the AI understand your unique voice and style.
                </p>
              </div>
              <div className="bg-gray-50 dark:bg-gray-800 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
                <div className="w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center mb-4">
                  <span className="text-lg font-bold text-amber-600">3</span>
                </div>
                <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">
                  Define Words to Avoid
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  List words and phrases that do not fit your brand. This helps
                  ensure generated content stays authentic to your voice.
                </p>
              </div>
            </div>
          </m.div>
        </div>
      </section>

      <SiteFooter />
    </main>
  )
}

export default function BrandPageClient() {
  return useBrandPageView()
}
