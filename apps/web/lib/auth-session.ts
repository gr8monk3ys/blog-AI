import 'server-only'

import { headers } from 'next/headers'
import { getAuth } from './auth'

/** The signed-in user's id from a validated Better Auth session, or null. */
export async function getUserIdOrNull(): Promise<string | null> {
  const requestHeaders = await headers()
  const session = await getAuth().api.getSession({ headers: requestHeaders })
  return session?.user.id ?? null
}

export async function requireUserId(): Promise<string> {
  const userId = await getUserIdOrNull()
  if (!userId) {
    throw new Error('UNAUTHORIZED')
  }
  return userId
}
