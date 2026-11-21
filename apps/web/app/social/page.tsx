import type { Metadata } from 'next'
import { redirect } from 'next/navigation'
import { getUserIdOrNull } from '../../lib/auth-session'
import SocialPageClient from './SocialPageClient'

export const metadata: Metadata = {
  title: 'Social Media Scheduling',
  description:
    'Schedule posts, manage campaigns, and track analytics across Twitter, LinkedIn, Facebook, and Instagram.',
}

export default async function SocialPage() {
  const userId = await getUserIdOrNull()
  if (!userId) {
    redirect('/sign-in')
  }
  return <SocialPageClient />
}
