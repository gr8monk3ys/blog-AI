import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import BulkGenerationPageClient from './BulkGenerationPageClient'

export default async function BulkGenerationPage() {
  const { userId } = await auth()
  if (!userId) {
    redirect('/sign-in')
  }
  return <BulkGenerationPageClient />
}
