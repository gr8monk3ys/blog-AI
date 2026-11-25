import type { Metadata } from 'next'
import { redirect } from 'next/navigation'
import { getUserIdOrNull } from '../../lib/auth-session'
import RemixPageClient from './RemixPageClient'

export const metadata: Metadata = {
  title: 'Content Remix',
  description:
    'Transform existing content into new formats with AI while preserving intent, tone, and brand voice.',
}

export default async function RemixPage() {
  const userId = await getUserIdOrNull()
  if (!userId) {
    redirect('/sign-in')
  }
  return <RemixPageClient />
}
