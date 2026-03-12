import type { NextFetchEvent, NextRequest } from 'next/server'
import { NextResponse } from 'next/server'
import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server'

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
const isHostedProduction =
  isProduction &&
  (process.env.VERCEL_ENV === 'production' || process.env.ENFORCE_PROXY_AUTH_CONFIG === '1')
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

if (isHostedProduction && !clerkEnabled) {
  throw new Error('NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY is required in production')
}

if (isHostedProduction && !hasValidClerkPublishableKey) {
  throw new Error(
    'NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY must be a valid Clerk key in production (pk_test_... or pk_live_...)'
  )
}

if (isHostedProduction && !clerkSecretKey) {
  throw new Error('CLERK_SECRET_KEY is required in production')
}

if (isHostedProduction && !hasValidClerkSecretKey) {
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

const protectedProxy = clerkMiddleware(async (auth, req) => {
  if (isProtectedRoute(req)) {
    await auth.protect()
  }
})

function noopProxy(): NextResponse {
  return NextResponse.next()
}

export default function proxy(req: NextRequest, event: NextFetchEvent) {
  if (!clerkEnabled) {
    return noopProxy()
  }

  return protectedProxy(req, event)
}

export const config = {
  matcher: [
    '/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)',
  ],
}
