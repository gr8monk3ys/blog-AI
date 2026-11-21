import type { Metadata } from 'next'
import { redirect } from 'next/navigation'
import { getUserIdOrNull } from '../../lib/auth-session'
import HistoryPageClient from './HistoryPageClient'

export const metadata: Metadata = {
  title: 'Content History',
  description:
    'Browse, filter, and manage your previously generated AI content, including favorites and recent outputs.',
}

export default async function HistoryPage() {
  const userId = await getUserIdOrNull()
  if (!userId) {
    redirect('/sign-in')
  }
  return <HistoryPageClient />
}
