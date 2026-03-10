import type { Metadata } from 'next'
import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'
import { getClerkUserIdOrNull } from '../../lib/clerk-auth'
import OnboardingPageClient from './OnboardingPageClient'

export const metadata: Metadata = {
  title: 'Onboarding | Blog AI',
  description:
    'Set up your Blog AI workspace and preferences to personalize your content generation experience.',
}

export default async function OnboardingPage() {
  const userId = await getClerkUserIdOrNull()
  if (!userId) {
    redirect('/sign-in')
  }

  const cookieStore = await cookies()
  if (cookieStore.get('onboarding_completed')?.value === 'true') {
    redirect('/bulk')
  }

  return <OnboardingPageClient />
}
