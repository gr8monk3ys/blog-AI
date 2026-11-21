import type { Metadata } from 'next'
import { redirect } from 'next/navigation'
import { getUserIdOrNull } from '../../lib/auth-session'
import TemplatesPageClient from './TemplatesPageClient'

export const metadata: Metadata = {
  title: 'Templates',
  description:
    'Use ready-to-run content templates for marketing, social, email, and blog workflows.',
}

export default async function TemplatesPage() {
  const userId = await getUserIdOrNull()
  if (!userId) {
    redirect('/sign-in')
  }
  return <TemplatesPageClient />
}
