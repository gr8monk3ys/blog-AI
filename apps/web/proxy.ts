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
const isDev = process.env.NODE_ENV === 'development'
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

// ---------------------------------------------------------------------------
// CSP nonce helper
// ---------------------------------------------------------------------------
// Builds a Content-Security-Policy header value that includes a per-request
// nonce.  When a nonce is present, spec-compliant browsers **ignore**
// 'unsafe-inline', but we keep it as a fallback for older browsers.

function buildCspHeader(nonce: string): string {
  const directives = [
    "default-src 'self'",

    // script-src
    [
      "script-src 'self'",
      `'nonce-${nonce}'`,
      "'unsafe-inline'",
      isDev ? "'unsafe-eval'" : '',
      'https://*.clerk.accounts.dev',
      'https://cdn.clerk.io',
      'https://challenges.cloudflare.com',
    ]
      .filter(Boolean)
      .join(' '),

    // style-src — nonce replaces blanket unsafe-inline
    [
      "style-src 'self'",
      `'nonce-${nonce}'`,
      "'unsafe-inline'",
    ].join(' '),

    "img-src 'self' data: https://*.clerk.com https://*.unsplash.com blob:",
    "font-src 'self' data:",

    // connect-src
    [
      "connect-src 'self'",
      'https://*.clerk.accounts.dev',
      'https://api.clerk.io',
      isDev ? 'ws://localhost:* wss://localhost:*' : '',
      process.env.NEXT_PUBLIC_API_URL || '',
    ]
      .filter(Boolean)
      .join(' '),

    "frame-src 'self' https://*.clerk.accounts.dev https://challenges.cloudflare.com",
    "frame-ancestors 'none'",
    "base-uri 'self'",
    "form-action 'self'",
  ]

  return directives.join('; ')
}

/**
 * Apply the CSP nonce to a response.  Generates a fresh nonce, sets the
 * `x-nonce` request header (readable in Server Components via `headers()`),
 * and writes the `Content-Security-Policy` response header.
 */
function applyNonce(
  response: NextResponse,
  nonce: string,
): void {
  response.headers.set('Content-Security-Policy', buildCspHeader(nonce))
}

export default function proxy(req: NextRequest, event: NextFetchEvent) {
  // Generate a per-request nonce for CSP
  const nonce = Buffer.from(crypto.randomUUID()).toString('base64')

  // Forward the nonce to Server Components via a request header
  const requestHeaders = new Headers(req.headers)
  requestHeaders.set('x-nonce', nonce)

  if (!hasValidClerkConfig) {
    if (isProduction && isProtectedRoute(req)) {
      const authUrl = new URL('/auth', req.url)
      authUrl.searchParams.set('reason', 'auth-not-configured')
      const redirectResponse = NextResponse.redirect(authUrl)
      applyNonce(redirectResponse, nonce)
      return redirectResponse
    }

    // No Clerk — pass through with nonce headers
    const response = NextResponse.next({
      request: { headers: requestHeaders },
    })
    applyNonce(response, nonce)
    return response
  }

  // Wrap the Clerk middleware and inject the nonce into the response it produces
  const clerkResponse = configuredClerkMiddleware(req, event)

  // clerkMiddleware may return a Response/NextResponse or undefined/void.
  // We need to handle both cases.
  if (clerkResponse instanceof Promise) {
    return clerkResponse.then((res) => {
      if (res) {
        // Clerk returned a response (redirect, rewrite, etc.)
        res.headers.set('Content-Security-Policy', buildCspHeader(nonce))
        // Forward nonce via a response header so layout can read it even when
        // Clerk has overridden the request headers.
        res.headers.set('x-nonce', nonce)
        return res
      }
      // Clerk returned nothing — create a passthrough response with nonce
      const passthroughResponse = NextResponse.next({
        request: { headers: requestHeaders },
      })
      applyNonce(passthroughResponse, nonce)
      return passthroughResponse
    })
  }

  // Synchronous return from Clerk (unlikely but handled for safety)
  if (clerkResponse) {
    const res = clerkResponse as NextResponse
    res.headers.set('Content-Security-Policy', buildCspHeader(nonce))
    res.headers.set('x-nonce', nonce)
    return res
  }

  const response = NextResponse.next({
    request: { headers: requestHeaders },
  })
  applyNonce(response, nonce)
  return response
}

export const config = {
  matcher: [
    '/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)',
  ],
}
