import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server'
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

const isProtectedRoute = createRouteMatcher([
  '/history(.*)',
  '/brand(.*)',
  '/admin(.*)',
  '/bulk(.*)',
  '/remix(.*)',
  '/analytics(.*)',
  '/tools(.*)',
  '/templates(.*)',
  '/onboarding(.*)',
])

const clerkEnabled = !!process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
const isProduction = process.env.NODE_ENV === 'production'
const suppressAuthWarning =
  process.env.SUPPRESS_PROXY_AUTH_WARNING === '1' ||
  process.env.PLAYWRIGHT_TEST === '1'
const clerkPublishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY ?? ''
const clerkSecretKey = process.env.CLERK_SECRET_KEY ?? ''
const hasValidClerkPublishableKey =
  clerkPublishableKey.startsWith('pk_test_') ||
  clerkPublishableKey.startsWith('pk_live_')
const hasValidClerkSecretKey =
  clerkSecretKey.startsWith('sk_test_') || clerkSecretKey.startsWith('sk_live_')

if (isProduction && !clerkEnabled) {
  throw new Error('NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY is required in production')
}

if (isProduction && !hasValidClerkPublishableKey) {
  throw new Error(
    'NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY must be a valid Clerk key in production (pk_test_... or pk_live_...)'
  )
}

if (isProduction && !clerkSecretKey) {
  throw new Error('CLERK_SECRET_KEY is required in production')
}

if (isProduction && !hasValidClerkSecretKey) {
  throw new Error(
    'CLERK_SECRET_KEY must be a valid Clerk key in production (sk_test_... or sk_live_...)'
  )
}

if (!clerkEnabled && !isProduction && !suppressAuthWarning) {
  console.warn(
    '[proxy] WARNING: NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY is not set. ' +
    'Authentication is disabled and all routes are publicly accessible. ' +
    'This is acceptable for local development only.'
  )
}

export default clerkEnabled
  ? clerkMiddleware(async (auth, req) => {
      if (isProtectedRoute(req)) {
        await auth.protect()
      }
    })
  : function passthroughMiddleware(_req: NextRequest): NextResponse {
      return NextResponse.next()
    }

export const config = {
  matcher: [
    '/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)',
  ],
}
