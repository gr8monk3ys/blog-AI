import type { Metadata } from 'next'
import { redirect } from 'next/navigation'
import { getClerkUserIdOrNull } from '../../lib/clerk-auth'
import GeneratePageClient from './GeneratePageClient'

export const metadata: Metadata = {
  title: 'Generate Content',
  description:
    'Generate brand-consistent blog posts with AI-powered research, fact-checking, and SEO optimization.',
}

export default async function GeneratePage() {
  const userId = await getClerkUserIdOrNull()
  if (!userId) {
    redirect('/sign-in')
  }
  return <GeneratePageClient />
}
