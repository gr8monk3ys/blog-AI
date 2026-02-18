import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import RemixPageClient from './RemixPageClient'

export default async function RemixPage() {
  const { userId } = await auth()
  if (!userId) {
    redirect('/sign-in')
  }
  return <RemixPageClient />
}
