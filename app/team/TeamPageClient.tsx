'use client'

import { useCallback, useEffect, useState } from 'react'
import { Tab } from '@headlessui/react'
import { UserGroupIcon, PlusIcon } from '@heroicons/react/24/outline'
import type { Organization, OrganizationMember, OrganizationInvite } from '../../types/team'
import { apiFetch, API_ENDPOINTS } from '../../lib/api'
import CreateOrgModal from '../../components/team/CreateOrgModal'
import MembersList from '../../components/team/MembersList'
import InviteForm from '../../components/team/InviteForm'

function classNames(...classes: string[]) {
  return classes.filter(Boolean).join(' ')
}

interface TeamPageState {
  orgs: Organization[]
  activeOrgId: string | null
  members: OrganizationMember[]
  invites: OrganizationInvite[]
  currentUserId: string
  currentUserRole: 'owner' | 'admin' | 'member' | 'viewer'
  showCreateModal: boolean
  loading: boolean
}

export default function TeamPageClient() {
  const [state, setState] = useState<TeamPageState>({
    orgs: [],
    activeOrgId: null,
    members: [],
    invites: [],
    currentUserId: '',
    currentUserRole: 'member',
    showCreateModal: false,
    loading: true,
  })

  const activeOrg = state.orgs.find((org) => org.id === state.activeOrgId) ?? null

  const fetchOrgs = useCallback(async () => {
    try {
      const data = await apiFetch<{ success: boolean; data: Organization[] }>(
        API_ENDPOINTS.organizations.list
      )
      if (data.success) {
        setState((current) => ({
          ...current,
          orgs: data.data,
          activeOrgId:
            current.activeOrgId && data.data.some((org) => org.id === current.activeOrgId)
              ? current.activeOrgId
              : (data.data[0]?.id ?? null),
        }))
      }
    } catch {
      // No orgs yet — that's fine
    } finally {
      setState((current) => ({ ...current, loading: false }))
    }
  }, [])

  const fetchOrgDetails = useCallback(async () => {
    if (!activeOrg) return
    try {
      const [membersRes, invitesRes] = await Promise.all([
        apiFetch<{ success: boolean; data: OrganizationMember[]; current_user_id?: string; current_role?: string }>(
          API_ENDPOINTS.organizations.members(activeOrg.id)
        ),
        apiFetch<{ success: boolean; data: OrganizationInvite[] }>(
          API_ENDPOINTS.organizations.invites(activeOrg.id)
        ).catch(() => ({ success: true, data: [] })),
      ])
      if (membersRes.success) {
        setState((current) => ({
          ...current,
          members: membersRes.data,
          currentUserId: membersRes.current_user_id || current.currentUserId,
          currentUserRole:
            (membersRes.current_role as TeamPageState['currentUserRole'] | undefined) ||
            current.currentUserRole,
        }))
      }
      if (invitesRes.success) {
        setState((current) => ({
          ...current,
          invites: invitesRes.data,
        }))
      }
    } catch {
      // Ignore
    }
  }, [activeOrg])

  useEffect(() => { fetchOrgs() }, [fetchOrgs])
  useEffect(() => { fetchOrgDetails() }, [fetchOrgDetails])

  if (state.loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-12">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 dark:bg-gray-800 rounded w-48" />
          <div className="h-64 bg-gray-200 dark:bg-gray-800 rounded" />
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-3">
          <UserGroupIcon className="h-6 w-6 text-amber-600" />
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Team</h1>
        </div>
        <button
          onClick={() => setState((current) => ({ ...current, showCreateModal: true }))}
          className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-amber-600 rounded-lg hover:bg-amber-700 transition-colors"
        >
          <PlusIcon className="h-4 w-4" />
          New Organization
        </button>
      </div>

      {state.orgs.length === 0 ? (
        <div className="text-center py-16 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800">
          <UserGroupIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-4 text-sm font-medium text-gray-900 dark:text-gray-100">No organizations</h3>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Create an organization to collaborate with your team.
          </p>
        </div>
      ) : (
        <>
          {/* Org selector */}
          {state.orgs.length > 1 && (
            <div className="mb-6">
              <select
                value={state.activeOrgId || ''}
                onChange={(e) =>
                  setState((current) => ({
                    ...current,
                    activeOrgId: e.target.value || null,
                  }))
                }
                className="rounded-md border-gray-300 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-100 focus:border-amber-500 focus:ring-amber-500"
              >
                {state.orgs.map((org) => (
                  <option key={org.id} value={org.id}>{org.name}</option>
                ))}
              </select>
            </div>
          )}

          {activeOrg && (
            <Tab.Group>
              <Tab.List className="flex space-x-1 rounded-lg bg-gray-100 dark:bg-gray-800 p-1 mb-6">
                {['Members', 'Invites', 'Settings'].map((tab) => (
                  <Tab
                    key={tab}
                    className={({ selected }) =>
                      classNames(
                        'w-full rounded-md py-2 text-sm font-medium leading-5 transition-colors',
                        selected
                          ? 'bg-white dark:bg-gray-900 text-amber-700 dark:text-amber-400 shadow'
                          : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
                      )
                    }
                  >
                    {tab}
                  </Tab>
                ))}
              </Tab.List>
              <Tab.Panels>
                {/* Members */}
                <Tab.Panel>
                  <MembersList
                    orgId={activeOrg.id}
                    members={state.members}
                    currentUserId={state.currentUserId}
                    currentUserRole={state.currentUserRole}
                    onMemberUpdated={fetchOrgDetails}
                  />
                </Tab.Panel>

                {/* Invites */}
                <Tab.Panel className="space-y-6">
                  {(state.currentUserRole === 'owner' || state.currentUserRole === 'admin') && (
                    <InviteForm orgId={activeOrg.id} onInviteSent={fetchOrgDetails} />
                  )}
                  {state.invites.length > 0 ? (
                    <div className="space-y-2">
                      {state.invites.map((invite) => (
                        <div
                          key={invite.id}
                          className="flex items-center justify-between px-4 py-3 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800"
                        >
                          <div>
                            <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{invite.email}</p>
                            <p className="text-xs text-gray-500 dark:text-gray-400">
                              {invite.role} &middot; {invite.status}
                            </p>
                          </div>
                          <span className="text-xs text-gray-400">
                            Expires {new Date(invite.expires_at).toLocaleDateString()}
                          </span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-gray-500 dark:text-gray-400">No pending invites.</p>
                  )}
                </Tab.Panel>

                {/* Settings */}
                <Tab.Panel>
                  <div className="space-y-4">
                    <div>
                      <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">Organization Name</h3>
                      <p className="mt-1 text-sm text-gray-900 dark:text-gray-100">{activeOrg.name}</p>
                    </div>
                    <div>
                      <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">Slug</h3>
                      <p className="mt-1 text-sm text-gray-900 dark:text-gray-100">{activeOrg.slug}</p>
                    </div>
                    <div>
                      <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">Plan</h3>
                      <p className="mt-1 text-sm text-gray-900 dark:text-gray-100 capitalize">{activeOrg.plan_tier}</p>
                    </div>
                  </div>
                </Tab.Panel>
              </Tab.Panels>
            </Tab.Group>
          )}
        </>
      )}

      <CreateOrgModal
        open={state.showCreateModal}
        onClose={() => setState((current) => ({ ...current, showCreateModal: false }))}
        onCreated={fetchOrgs}
      />
    </div>
  )
}
