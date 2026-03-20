import type { Metadata } from 'next'
import { redirect } from 'next/navigation'
import { getClerkUserIdOrNull } from '../../lib/clerk-auth'
import PlagiarismPageClient from './PlagiarismPageClient'

export const metadata: Metadata = {
  title: 'Plagiarism Detection',
  description:
    'Check your content for plagiarism before publishing. Multi-provider scanning with detailed source matching.',
}

export default async function PlagiarismPage() {
  const userId = await getClerkUserIdOrNull()
  if (!userId) {
    redirect('/sign-in')
  }
  return <PlagiarismPageClient />
}
