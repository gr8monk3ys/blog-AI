import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server'
import { NextFetchEvent, NextRequest, NextResponse } from 'next/server'

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

const hasValidClerkConfig =
  clerkEnabled &&
  hasValidClerkPublishableKey &&
  !!clerkSecretKey &&
  hasValidClerkSecretKey

if (isProduction && !hasValidClerkConfig) {
  console.warn(
    '[proxy] Clerk is not fully configured in production. ' +
    'Public routes will remain available, but protected routes will redirect to /auth.'
  )
}

if (!clerkEnabled && !isProduction && !suppressAuthWarning) {
  console.warn(
    '[proxy] WARNING: NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY is not set. ' +
    'Authentication is disabled and all routes are publicly accessible. ' +
    'This is acceptable for local development only.'
  )
}

const configuredClerkMiddleware = clerkMiddleware(async (auth, req) => {
  if (isProtectedRoute(req)) {
    await auth.protect()
  }
})

export default function proxy(req: NextRequest, event: NextFetchEvent) {
  if (!hasValidClerkConfig) {
    if (isProtectedRoute(req)) {
      const authUrl = new URL('/auth', req.url)
      authUrl.searchParams.set('reason', 'auth-not-configured')
      return NextResponse.redirect(authUrl)
    }
    return
  }

  return configuredClerkMiddleware(req, event)
}

export const config = {
  matcher: [
    '/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)',
  ],
}
