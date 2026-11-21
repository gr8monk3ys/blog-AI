import type { Metadata } from 'next'
import { redirect } from 'next/navigation'
import { getUserIdOrNull } from '../../../lib/auth-session'
import VoiceTrainingPageClient from './VoiceTrainingPageClient'

export const metadata: Metadata = {
  title: 'Train Brand Voice',
  description:
    'Train your custom brand voice with writing samples so generated content stays consistent with your style.',
}

export default async function VoiceTrainingPage() {
  const userId = await getUserIdOrNull()
  if (!userId) {
    redirect('/sign-in')
  }
  return <VoiceTrainingPageClient />
}
