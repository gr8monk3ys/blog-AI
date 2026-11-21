import type { Metadata } from 'next'
import { redirect } from 'next/navigation'
import { getUserIdOrNull } from '../../../lib/auth-session'
import WebhooksPageClient from './WebhooksPageClient'

export const metadata: Metadata = {
  title: 'Webhook Management',
  description:
    'Manage webhook subscriptions for real-time event notifications from your content pipeline.',
}

export default async function WebhooksPage() {
  const userId = await getUserIdOrNull()
  if (!userId) {
    redirect('/sign-in')
  }
  return <WebhooksPageClient />
}
