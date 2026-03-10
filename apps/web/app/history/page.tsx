import type { Metadata } from 'next'
import { redirect } from 'next/navigation'
import { getClerkUserIdOrNull } from '../../lib/clerk-auth'
import HistoryPageClient from './HistoryPageClient'

export const metadata: Metadata = {
  title: 'Content History | Blog AI',
  description:
    'Browse, filter, and manage your previously generated AI content, including favorites and recent outputs.',
}

export default async function HistoryPage() {
  const userId = await getClerkUserIdOrNull()
  if (!userId) {
    redirect('/sign-in')
  }
  return <HistoryPageClient />
}
