'use client'

import { useEffect, useState } from 'react'
import type { Organization } from '../../types/team'
import { apiFetch, API_ENDPOINTS } from '../../lib/api'

interface OrgSelectorProps {
  activeOrgId: string | null
  onSelect: (orgId: string | null) => void
}

export default function OrgSelector({ activeOrgId, onSelect }: OrgSelectorProps) {
  const [orgs, setOrgs] = useState<Organization[]>([])

  useEffect(() => {
    let mounted = true
    ;(async () => {
      try {
        const data = await apiFetch<{ success: boolean; data: Organization[] }>(
          API_ENDPOINTS.organizations.list
        )
        if (mounted && data.success) {
          setOrgs(data.data)
        }
      } catch {
        // Silently ignore — org list is optional
      }
    })()
    return () => { mounted = false }
  }, [])

  if (orgs.length === 0) return null

  return (
    <select
      value={activeOrgId || ''}
      onChange={(e) => onSelect(e.target.value || null)}
      className="text-xs rounded border-gray-300 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-100 focus:border-amber-500 focus:ring-amber-500"
      aria-label="Select organization"
    >
      <option value="">Personal</option>
      {orgs.map((org) => (
        <option key={org.id} value={org.id}>
          {org.name}
        </option>
      ))}
    </select>
  )
}
