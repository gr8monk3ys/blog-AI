import type { Metadata } from 'next'
import { redirect } from 'next/navigation'
import { getClerkUserIdOrNull } from '../../lib/clerk-auth'
import SocialPageClient from './SocialPageClient'

export const metadata: Metadata = {
  title: 'Social Media Scheduling',
  description:
    'Schedule posts, manage campaigns, and track analytics across Twitter, LinkedIn, Facebook, and Instagram.',
}

export default async function SocialPage() {
  const userId = await getClerkUserIdOrNull()
  if (!userId) {
    redirect('/sign-in')
  }
  return <SocialPageClient />
}
