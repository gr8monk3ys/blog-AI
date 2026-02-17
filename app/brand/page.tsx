import { auth } from '@clerk/nextjs/server'
import { redirect } from 'next/navigation'
import BrandPageClient from './BrandPageClient'

export default async function BrandPage() {
  const { userId } = await auth()
  if (!userId) {
    redirect('/sign-in')
  }
  return <BrandPageClient />
}
