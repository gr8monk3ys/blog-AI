import type { Metadata } from 'next'
import { redirect } from 'next/navigation'
import { getUserIdOrNull } from '../../lib/auth-session'
import TeamPageClient from './TeamPageClient'

export const metadata: Metadata = {
  title: 'Team',
  description: 'Manage your organization, team members, invitations, and billing.',
}

export default async function TeamPage() {
  const userId = await getUserIdOrNull()
  if (!userId) {
    redirect('/sign-in')
  }
  return <TeamPageClient />
}
