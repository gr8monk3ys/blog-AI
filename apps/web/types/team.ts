/**
 * Types for team/organization management
 */

export type OrganizationRole = 'owner' | 'admin' | 'member' | 'viewer'

export interface Organization {
  id: string
  name: string
  slug: string
  plan_tier: string
  created_by: string
  created_at: string
  settings?: Record<string, unknown>
}

export interface OrganizationMember {
  user_id: string
  email?: string
  role: OrganizationRole
  joined_at: string
  invited_by?: string
}

export interface OrganizationInvite {
  id: string
  email: string
  role: OrganizationRole
  status: 'pending' | 'accepted' | 'expired' | 'revoked'
  expires_at: string
  created_at: string
}
