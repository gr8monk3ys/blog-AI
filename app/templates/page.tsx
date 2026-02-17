import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import TemplatesPageClient from './TemplatesPageClient'

export default async function TemplatesPage() {
  const { userId } = await auth()
  if (!userId) {
    redirect('/sign-in')
  }
  return <TemplatesPageClient />
}
