import 'server-only'

import { auth } from '@clerk/nextjs/server'

const clerkEnabled = !!process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
const isProduction = process.env.NODE_ENV === 'production'

export function isClerkEnabled(): boolean {
  return clerkEnabled
}

export async function getClerkUserIdOrNull(): Promise<string | null> {
  if (!clerkEnabled) {
    // Local development mode without Clerk configured stays permissive.
    // Production must fail closed and treat the user as unauthenticated.
    return isProduction ? null : 'dev-local-user'
  }

  const { userId } = await auth()
  return userId || null
}

export async function requireClerkUserId(): Promise<string> {
  const userId = await getClerkUserIdOrNull()
  if (!userId) {
    throw new Error('UNAUTHORIZED')
  }
  return userId
}
