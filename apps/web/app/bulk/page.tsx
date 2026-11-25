import type { Metadata } from 'next'
import { redirect } from 'next/navigation'
import { getUserIdOrNull } from '../../lib/auth-session'
import BulkGenerationPageClient from './BulkGenerationPageClient'

export const metadata: Metadata = {
  title: 'Bulk Generation',
  description:
    'Generate multiple pieces of content in one run with CSV upload, provider strategy controls, and export options.',
}

export default async function BulkGenerationPage() {
  const userId = await getUserIdOrNull()
  if (!userId) {
    redirect('/sign-in')
  }
  return <BulkGenerationPageClient />
}
