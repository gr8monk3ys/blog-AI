import type { Metadata } from 'next'
import { redirect } from 'next/navigation'
import { getUserIdOrNull } from '../../lib/auth-session'
import GeneratePageClient from './GeneratePageClient'

export const metadata: Metadata = {
  title: 'Generate Content',
  description:
    'Generate brand-consistent blog posts with AI-powered research, fact-checking, and SEO optimization.',
}

export default async function GeneratePage() {
  const userId = await getUserIdOrNull()
  if (!userId) {
    redirect('/sign-in')
  }
  return <GeneratePageClient />
}
