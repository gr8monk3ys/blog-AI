import type { Metadata } from 'next'
import { redirect } from 'next/navigation'
import { getClerkUserIdOrNull } from '../../../lib/clerk-auth'
import ScorePageClient from './ScorePageClient'

export const metadata: Metadata = {
  title: 'Score Content | Brand Voice | Blog AI',
  description: 'Score your content against your trained brand voice profile.',
}

export default async function ScorePage() {
  const userId = await getClerkUserIdOrNull()
  if (!userId) {
    redirect('/sign-in')
  }
  return <ScorePageClient />
}
