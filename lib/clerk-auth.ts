import 'server-only'

import { auth } from '@clerk/nextjs/server'

export async function getClerkUserIdOrNull(): Promise<string | null> {
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
