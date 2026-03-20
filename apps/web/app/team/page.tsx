import type { Metadata } from 'next'
import { redirect } from 'next/navigation'
import { getClerkUserIdOrNull } from '../../lib/clerk-auth'
import TeamPageClient from './TeamPageClient'

export const metadata: Metadata = {
  title: 'Team',
  description: 'Manage your organization, team members, invitations, and billing.',
}

export default async function TeamPage() {
  const userId = await getClerkUserIdOrNull()
  if (!userId) {
    redirect('/sign-in')
  }
  return <TeamPageClient />
}
