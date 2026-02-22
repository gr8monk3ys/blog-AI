import type { Metadata } from 'next'
import { redirect } from 'next/navigation'
import { getClerkUserIdOrNull } from '../../../lib/clerk-auth'
import VoiceTrainingPageClient from './VoiceTrainingPageClient'

export const metadata: Metadata = {
  title: 'Train Brand Voice | Blog AI',
  description:
    'Train your custom brand voice with writing samples so generated content stays consistent with your style.',
}

export default async function VoiceTrainingPage() {
  const userId = await getClerkUserIdOrNull()
  if (!userId) {
    redirect('/sign-in')
  }
  return <VoiceTrainingPageClient />
}
