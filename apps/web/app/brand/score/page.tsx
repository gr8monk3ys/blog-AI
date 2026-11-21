import type { Metadata } from 'next'
import { redirect } from 'next/navigation'
import { getUserIdOrNull } from '../../../lib/auth-session'
import ScorePageClient from './ScorePageClient'

export const metadata: Metadata = {
  title: 'Score Content — Brand Voice',
  description: 'Score your content against your trained brand voice profile.',
}

export default async function ScorePage() {
  const userId = await getUserIdOrNull()
  if (!userId) {
    redirect('/sign-in')
  }
  return <ScorePageClient />
}
