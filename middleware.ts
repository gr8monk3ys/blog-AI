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

if (isProduction && !clerkEnabled) {
  throw new Error('NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY is required in production')
}

if (!clerkEnabled && !isProduction) {
  console.warn(
    '[middleware] WARNING: NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY is not set. ' +
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
