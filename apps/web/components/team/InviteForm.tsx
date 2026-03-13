'use client'

import { useState } from 'react'
import type { OrganizationRole } from '../../types/team'
import { apiFetch, API_ENDPOINTS } from '../../lib/api'

interface InviteFormProps {
  orgId: string
  onInviteSent: () => void
}

const INVITABLE_ROLES: OrganizationRole[] = ['admin', 'member', 'viewer']

export default function InviteForm({ orgId, onInviteSent }: InviteFormProps) {
  const [email, setEmail] = useState('')
  const [role, setRole] = useState<OrganizationRole>('member')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email.trim()) return

    setLoading(true)
    setError(null)
    setSuccess(false)

    try {
      await apiFetch(API_ENDPOINTS.organizations.invite(orgId), {
        method: 'POST',
        body: JSON.stringify({ email: email.trim(), role }),
      })
      setEmail('')
      setSuccess(true)
      onInviteSent()
      setTimeout(() => setSuccess(false), 3000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send invite')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex items-end gap-3">
      <div className="flex-1">
        <label htmlFor="invite-email" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
          Invite by email
        </label>
        <input
          id="invite-email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-700 shadow-sm focus:border-amber-500 focus:ring-amber-500 dark:bg-gray-800 dark:text-gray-100"
          placeholder="colleague@company.com"
          required
        />
      </div>

      <div>
        <label htmlFor="invite-role" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
          Role
        </label>
        <select
          id="invite-role"
          value={role}
          onChange={(e) => setRole(e.target.value as OrganizationRole)}
          className="mt-1 block rounded-md border-gray-300 dark:border-gray-700 shadow-sm focus:border-amber-500 focus:ring-amber-500 dark:bg-gray-800 dark:text-gray-100"
        >
          {INVITABLE_ROLES.map((r) => (
            <option key={r} value={r}>{r}</option>
          ))}
        </select>
      </div>

      <button
        type="submit"
        disabled={loading || !email.trim()}
        className="px-4 py-2 text-sm font-medium text-white bg-amber-600 border border-transparent rounded-lg hover:bg-amber-700 focus:ring-2 focus:ring-offset-2 focus:ring-amber-500 transition-colors disabled:opacity-50"
      >
        {loading ? 'Sending...' : 'Send Invite'}
      </button>

      {error && <p className="text-sm text-red-600 dark:text-red-400">{error}</p>}
      {success && <p className="text-sm text-emerald-600 dark:text-emerald-400">Invite sent!</p>}
    </form>
  )
}
