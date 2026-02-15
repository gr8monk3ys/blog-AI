import { clerkMiddleware } from '@clerk/nextjs/server'

// Clerk middleware is required for Clerk auth() in App Router and for route
// protection. We intentionally do not protect routes here yet; individual pages
// and API routes enforce auth where needed.
export default clerkMiddleware()

export const config = {
  matcher: [
    // Skip Next.js internals and all static files, but run middleware on routes
    // and route handlers.
    '/((?!_next|.*\\..*).*)',
    '/',
    '/(api|trpc)(.*)',
  ],
}

