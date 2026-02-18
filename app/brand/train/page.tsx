import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import VoiceTrainingPageClient from './VoiceTrainingPageClient'

export default async function VoiceTrainingPage() {
  const { userId } = await auth()
  if (!userId) {
    redirect('/sign-in')
  }
  return <VoiceTrainingPageClient />
}
