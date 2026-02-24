'use client'

import { useState } from 'react'
import type { OrganizationMember, OrganizationRole } from '../../types/team'
import { apiFetch, API_ENDPOINTS } from '../../lib/api'

interface MembersListProps {
  orgId: string
  members: OrganizationMember[]
  currentUserId: string
  currentUserRole: OrganizationRole
  onMemberUpdated: () => void
}

const ROLE_COLORS: Record<OrganizationRole, string> = {
  owner: 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400',
  admin: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400',
  member: 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-400',
  viewer: 'bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-500',
}

const ASSIGNABLE_ROLES: OrganizationRole[] = ['admin', 'member', 'viewer']

export default function MembersList({
  orgId,
  members,
  currentUserId,
  currentUserRole,
  onMemberUpdated,
}: MembersListProps) {
  const [updatingUser, setUpdatingUser] = useState<string | null>(null)
  const canManage = currentUserRole === 'owner' || currentUserRole === 'admin'

  const handleRoleChange = async (userId: string, newRole: OrganizationRole) => {
    setUpdatingUser(userId)
    try {
      await apiFetch(API_ENDPOINTS.organizations.updateMember(orgId, userId), {
        method: 'PATCH',
        body: JSON.stringify({ role: newRole }),
      })
      onMemberUpdated()
    } catch (err) {
      console.error('Failed to update member role:', err)
    } finally {
      setUpdatingUser(null)
    }
  }

  const handleRemove = async (userId: string) => {
    if (!confirm('Remove this member from the organization?')) return
    setUpdatingUser(userId)
    try {
      await apiFetch(API_ENDPOINTS.organizations.removeMember(orgId, userId), {
        method: 'DELETE',
      })
      onMemberUpdated()
    } catch (err) {
      console.error('Failed to remove member:', err)
    } finally {
      setUpdatingUser(null)
    }
  }

  return (
    <div className="overflow-hidden border border-gray-200 dark:border-gray-800 rounded-lg">
      <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-800">
        <thead className="bg-gray-50 dark:bg-gray-900">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Member
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Role
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Joined
            </th>
            {canManage && (
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Actions
              </th>
            )}
          </tr>
        </thead>
        <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-800">
          {members.map((member) => {
            const isSelf = member.user_id === currentUserId
            const isOwner = member.role === 'owner'
            const isUpdating = updatingUser === member.user_id

            return (
              <tr key={member.user_id} className={isUpdating ? 'opacity-50' : ''}>
                <td className="px-4 py-3 text-sm text-gray-900 dark:text-gray-100">
                  <div className="flex items-center gap-2">
                    <div className="w-7 h-7 rounded-full bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center text-xs font-medium text-amber-700 dark:text-amber-400">
                      {(member.email || member.user_id).charAt(0).toUpperCase()}
                    </div>
                    <span className="truncate max-w-[200px]">
                      {member.email || member.user_id.slice(0, 12) + '...'}
                    </span>
                    {isSelf && (
                      <span className="text-xs text-gray-400">(you)</span>
                    )}
                  </div>
                </td>
                <td className="px-4 py-3">
                  <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${ROLE_COLORS[member.role]}`}>
                    {member.role}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">
                  {new Date(member.joined_at).toLocaleDateString()}
                </td>
                {canManage && (
                  <td className="px-4 py-3 text-right">
                    {!isOwner && !isSelf && (
                      <div className="flex items-center justify-end gap-2">
                        <select
                          value={member.role}
                          onChange={(e) => handleRoleChange(member.user_id, e.target.value as OrganizationRole)}
                          disabled={isUpdating}
                          className="text-xs rounded border-gray-300 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-100"
                        >
                          {ASSIGNABLE_ROLES.map((r) => (
                            <option key={r} value={r}>{r}</option>
                          ))}
                        </select>
                        <button
                          onClick={() => handleRemove(member.user_id)}
                          disabled={isUpdating}
                          className="text-xs text-red-600 hover:text-red-700 dark:text-red-400"
                        >
                          Remove
                        </button>
                      </div>
                    )}
                  </td>
                )}
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
