import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import AnalyticsPageClient from './AnalyticsPageClient'

export default async function AnalyticsPage() {
  const { userId } = await auth()
  if (!userId) {
    redirect('/sign-in')
  }
  return <AnalyticsPageClient />
}
