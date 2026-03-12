'use client'

import { useState } from 'react'
import type { OrganizationRole } from '../../types/team'
import { apiFetch, API_ENDPOINTS } from '../../lib/api'

interface InviteFormProps {
  orgId: string
  onInviteSent: () => void
}

const INVITABLE_ROLES: OrganizationRole[] = ['admin', 'member', 'viewer']

interface InviteFormState {
  email: string
  role: OrganizationRole
  loading: boolean
  feedback: {
    type: 'error' | 'success' | null
    message: string
  }
}

export default function InviteForm({ orgId, onInviteSent }: InviteFormProps) {
  const [state, setState] = useState<InviteFormState>({
    email: '',
    role: 'member',
    loading: false,
    feedback: {
      type: null,
      message: '',
    },
  })

  const { email, role, loading, feedback } = state

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email.trim()) return

    setState((current) => ({
      ...current,
      loading: true,
      feedback: { type: null, message: '' },
    }))

    try {
      await apiFetch(API_ENDPOINTS.organizations.invite(orgId), {
        method: 'POST',
        body: JSON.stringify({ email: email.trim(), role }),
      })
      setState((current) => ({
        ...current,
        email: '',
        loading: false,
        feedback: { type: 'success', message: 'Invite sent!' },
      }))
      onInviteSent()
      setTimeout(() => {
        setState((current) =>
          current.feedback.type === 'success'
            ? { ...current, feedback: { type: null, message: '' } }
            : current
        )
      }, 3000)
    } catch (err) {
      setState((current) => ({
        ...current,
        loading: false,
        feedback: {
          type: 'error',
          message: err instanceof Error ? err.message : 'Failed to send invite',
        },
      }))
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
          onChange={(e) =>
            setState((current) => ({
              ...current,
              email: e.target.value,
            }))
          }
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
          onChange={(e) =>
            setState((current) => ({
              ...current,
              role: e.target.value as OrganizationRole,
            }))
          }
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

      {feedback.type === 'error' && (
        <p className="text-sm text-red-600 dark:text-red-400">{feedback.message}</p>
      )}
      {feedback.type === 'success' && (
        <p className="text-sm text-emerald-600 dark:text-emerald-400">{feedback.message}</p>
      )}
    </form>
  )
}
