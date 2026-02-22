import 'server-only'

import { auth } from '@clerk/nextjs/server'

const clerkEnabled = !!process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY

export function isClerkEnabled(): boolean {
  return clerkEnabled
}

export async function getClerkUserIdOrNull(): Promise<string | null> {
  if (!clerkEnabled) {
    // Local development mode without Clerk configured.
    // Middleware is intentionally permissive in this mode.
    return 'dev-local-user'
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
