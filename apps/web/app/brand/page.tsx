import type { Metadata } from 'next'
import { redirect } from 'next/navigation'
import { getUserIdOrNull } from '../../lib/auth-session'
import BrandPageClient from './BrandPageClient'

export const metadata: Metadata = {
  title: 'Brand Voice Profiles',
  description:
    'Create and manage brand voice profiles to keep generated content aligned with your tone and audience.',
}

export default async function BrandPage() {
  const userId = await getUserIdOrNull()
  if (!userId) {
    redirect('/sign-in')
  }
  return <BrandPageClient />
}
