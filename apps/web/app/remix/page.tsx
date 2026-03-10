import type { Metadata } from 'next'
import { redirect } from 'next/navigation'
import { getClerkUserIdOrNull } from '../../lib/clerk-auth'
import RemixPageClient from './RemixPageClient'

export const metadata: Metadata = {
  title: 'Content Remix | Blog AI',
  description:
    'Transform existing content into new formats with AI while preserving intent, tone, and brand voice.',
}

export default async function RemixPage() {
  const userId = await getClerkUserIdOrNull()
  if (!userId) {
    redirect('/sign-in')
  }
  return <RemixPageClient />
}
