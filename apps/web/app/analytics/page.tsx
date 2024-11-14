import type { Metadata } from 'next'
import { redirect } from 'next/navigation'
import { getClerkUserIdOrNull } from '../../lib/clerk-auth'
import AnalyticsPageClient from './AnalyticsPageClient'

export const metadata: Metadata = {
  title: 'Analytics',
  description:
    'Track content generation trends, tool usage, and performance insights across your Blog AI workspace.',
}

export default async function AnalyticsPage() {
  const userId = await getClerkUserIdOrNull()
  if (!userId) {
    redirect('/sign-in')
  }
  return <AnalyticsPageClient />
}
