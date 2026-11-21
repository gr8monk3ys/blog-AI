import { getSessionCookie } from 'better-auth/cookies'
import { NextRequest, NextResponse } from 'next/server'
import { isProtectedPath } from './lib/protected-routes'

const isDev = process.env.NODE_ENV === 'development'

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
    ]
      .filter(Boolean)
      .join(' '),

    // style-src. No nonce here on purpose: once a nonce is present, browsers
    // ignore 'unsafe-inline' for styles, and inline `style=""` attributes have
    // no way to carry a nonce. Production was logging ~500 style violations
    // per page load and silently dropping them: framer-motion's animated
    // transforms and the hero's radial-gradient backgrounds never applied.
    // The nonce stays on script-src, which is where it earns its keep.
    "style-src 'self' 'unsafe-inline'",

    // Sentry Session Replay compresses in a Worker created from a blob: URL.
    "worker-src 'self' blob:",

    "img-src 'self' data: https://*.unsplash.com blob:",
    "font-src 'self' data:",

    // connect-src
    [
      "connect-src 'self'",
      isDev ? 'ws://localhost:* wss://localhost:*' : '',
      process.env.NEXT_PUBLIC_API_URL || '',
      // Sentry browser SDK. The US-region ingest host is
      // `<org>.ingest.us.sentry.io`; without this every envelope is refused
      // by CSP and browser errors never reach the project.
      'https://*.ingest.us.sentry.io',
      'https://*.ingest.sentry.io',
    ]
      .filter(Boolean)
      .join(' '),

    "frame-src 'self'",
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

export default function proxy(req: NextRequest) {
  // Generate a per-request nonce for CSP
  const nonce = Buffer.from(crypto.randomUUID()).toString('base64')

  // Cookie presence only: an optimistic redirect for signed-out visitors.
  // Protected pages validate the session server-side (lib/auth-session.ts).
  if (isProtectedPath(req.nextUrl.pathname) && !getSessionCookie(req)) {
    const signInUrl = new URL('/sign-in', req.url)
    signInUrl.searchParams.set('redirect', req.nextUrl.pathname + req.nextUrl.search)
    const redirectResponse = NextResponse.redirect(signInUrl)
    applyNonce(redirectResponse, nonce)
    return redirectResponse
  }

  // Forward the nonce to Server Components via a request header
  const requestHeaders = new Headers(req.headers)
  requestHeaders.set('x-nonce', nonce)
  const response = NextResponse.next({
    request: { headers: requestHeaders },
  })
  applyNonce(response, nonce)
  return response
}

export const config = {
  matcher: [
    '/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)$).*)',
  ],
}
