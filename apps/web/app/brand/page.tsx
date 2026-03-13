import type { Metadata } from 'next'
import { redirect } from 'next/navigation'
import { getClerkUserIdOrNull } from '../../lib/clerk-auth'
import BrandPageClient from './BrandPageClient'

export const metadata: Metadata = {
  title: 'Brand Voice Profiles | Blog AI',
  description:
    'Create and manage brand voice profiles to keep generated content aligned with your tone and audience.',
}

export default async function BrandPage() {
  const userId = await getClerkUserIdOrNull()
  if (!userId) {
    redirect('/sign-in')
  }
  return <BrandPageClient />
}
