/** @type {import('next').NextConfig} */
import { withSentryConfig } from '@sentry/nextjs'
import { dirname } from 'path'
import { fileURLToPath } from 'url'

const __dirname = dirname(fileURLToPath(import.meta.url))

const isDev = process.env.NODE_ENV === 'development'

// =============================================================================
// Build-time environment validation for production deployments
// Only enforced in CI/Vercel (not local `bun run build`)
// =============================================================================
const isDeployBuild = process.env.CI === 'true' || process.env.VERCEL === '1'
const isVercelProductionBuild =
  process.env.NODE_ENV === 'production' &&
  isDeployBuild &&
  process.env.VERCEL_ENV === 'production'
const useStrictScriptCsp =
  process.env.VERCEL_ENV === 'production' || process.env.ENFORCE_STRICT_CSP === '1'

if (isVercelProductionBuild) {
  if (!process.env.NEXT_PUBLIC_API_URL) {
    throw new Error(
      'NEXT_PUBLIC_API_URL is required in production. ' +
      'Set it to your backend API URL (e.g. https://api.blogai.com).'
    )
  }
  if (!process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY) {
    throw new Error(
      'NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY is required in production. ' +
      'Set it to your Clerk publishable key for authentication.'
    )
  }
  if (!process.env.CLERK_SECRET_KEY) {
    throw new Error(
      'CLERK_SECRET_KEY is required in production. ' +
      'Set it to your Clerk secret key for server-side authentication.'
    )
  }
  if (
    !process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY.startsWith('pk_test_') &&
    !process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY.startsWith('pk_live_')
  ) {
    throw new Error(
      'NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY must be a valid Clerk key in production ' +
      '(pk_test_... or pk_live_...).'
    )
  }
  if (
    !process.env.CLERK_SECRET_KEY.startsWith('sk_test_') &&
    !process.env.CLERK_SECRET_KEY.startsWith('sk_live_')
  ) {
    throw new Error(
      'CLERK_SECRET_KEY must be a valid Clerk key in production (sk_test_... or sk_live_...).'
    )
  }
  if (process.env.NEXT_PUBLIC_API_URL.includes('localhost')) {
    console.warn(
      '[next.config] WARNING: NEXT_PUBLIC_API_URL contains "localhost". ' +
      'This is likely incorrect for a production build.'
    )
  }
}

// Bundle analyzer - only loaded when ANALYZE env var is set
const withBundleAnalyzer =
  process.env.ANALYZE === 'true'
    ? (await import('@next/bundle-analyzer')).default({ enabled: true })
    : (config) => config

// Security headers for production
const securityHeaders = [
  {
    // Enforce HTTPS
    key: 'Strict-Transport-Security',
    value: 'max-age=31536000; includeSubDomains; preload',
  },
  {
    // Prevent clickjacking
    key: 'X-Frame-Options',
    value: 'DENY',
  },
  {
    // Prevent MIME type sniffing
    key: 'X-Content-Type-Options',
    value: 'nosniff',
  },
  {
    // Control referrer information
    key: 'Referrer-Policy',
    value: 'strict-origin-when-cross-origin',
  },
  {
    // XSS protection for older browsers
    key: 'X-XSS-Protection',
    value: '1; mode=block',
  },
  {
    // Permissions policy - restrict sensitive APIs
    key: 'Permissions-Policy',
    value: 'camera=(), microphone=(), geolocation=(), interest-cohort=()',
  },
  {
    // Content Security Policy
    // In development, Next.js requires 'unsafe-eval' for fast refresh / HMR.
    // In production we drop it and restrict sources to known origins only.
    key: 'Content-Security-Policy',
    value: [
      "default-src 'self'",
      [
        "script-src 'self'",
        isDev ? "'unsafe-eval'" : '',
        useStrictScriptCsp ? '' : "'unsafe-inline'",
        'https://*.clerk.accounts.dev',
        'https://cdn.clerk.io',
        'https://challenges.cloudflare.com',
      ].filter(Boolean).join(' '),
      "style-src 'self' 'unsafe-inline'",
      "img-src 'self' data: https://*.clerk.com https://*.unsplash.com blob:",
      "font-src 'self' data:",
      [
        "connect-src 'self'",
        'https://*.clerk.accounts.dev',
        'https://api.clerk.io',
        isDev ? 'ws://localhost:* wss://localhost:*' : '',
        process.env.NEXT_PUBLIC_API_URL || '',
      ].filter(Boolean).join(' '),
      "frame-src 'self' https://*.clerk.accounts.dev https://challenges.cloudflare.com",
      "frame-ancestors 'none'",
      "base-uri 'self'",
      "form-action 'self'",
    ].join('; '),
  },
]

const nextConfig = {
  // Recommended: Strict mode for catching issues early
  reactStrictMode: true,

  // Turbopack configuration (Next.js 16+ default bundler)
  // Explicit root prevents incorrect monorepo/workspace inference when multiple
  // lockfiles exist elsewhere on disk.
  turbopack: { root: __dirname },

  // Remove X-Powered-By header for security
  poweredByHeader: false,

  // Enable gzip compression
  compress: true,

  // Experimental features
  experimental: {
    // Enable scroll restoration
    scrollRestoration: true,
  },

  // Image optimization with modern formats
  images: {
    // Enable modern image formats for better compression
    formats: ['image/avif', 'image/webp'],
    // Device sizes for responsive images
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    // Image sizes for layout optimization
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
    // Remote patterns for external images
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**.unsplash.com',
      },
    ],
    // Minimize image processing time
    minimumCacheTTL: 60 * 60 * 24 * 30, // 30 days
  },

  // Custom headers for security and caching
  async headers() {
    return [
      {
        // Apply security headers to all routes
        source: '/:path*',
        headers: securityHeaders,
      },
      {
        // Cache static assets aggressively
        source: '/static/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',
          },
        ],
      },
      {
        // Cache Next.js static files
        source: '/_next/static/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',
          },
        ],
      },
      {
        // Cache images with revalidation
        source: '/_next/image/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=86400, stale-while-revalidate=604800',
          },
        ],
      },
      {
        // Cache fonts
        source: '/fonts/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',
          },
        ],
      },
    ]
  },

  async rewrites() {
    return {
      beforeFiles: [
        {
          source: '/',
          destination: '/home.html',
        },
      ],
    }
  },

  // Webpack configuration for production optimizations
  webpack: (config, { dev, isServer }) => {
    // Ignore known noisy dependency warning from OpenTelemetry's dynamic require.
    // This warning originates in a third-party package used by Sentry/Prisma.
    config.ignoreWarnings = [
      ...(config.ignoreWarnings || []),
      (warning) => {
        const message =
          typeof warning === 'string'
            ? warning
            : (warning?.message ?? '')
        const moduleResource =
          typeof warning === 'object' &&
          typeof warning?.module === 'object' &&
          warning.module &&
          'resource' in warning.module
            ? String(warning.module.resource ?? '')
            : ''

        return (
          /Critical dependency: the request of a dependency is an expression/.test(message) &&
          /@opentelemetry\/instrumentation/.test(moduleResource)
        )
      },
    ]

    // Production optimizations
    if (!dev && !isServer) {
      // Enable tree shaking for better bundle size
      config.optimization = {
        ...config.optimization,
        usedExports: true,
        sideEffects: true,
      }
    }

    return config
  },
}

// Sentry configuration options
const sentryWebpackPluginOptions = {
  // Organization and project from environment
  org: process.env.SENTRY_ORG,
  project: process.env.SENTRY_PROJECT,

  // Only upload source maps if auth token is configured
  silent: true, // Suppress logs

  // Hide source maps from users (security)
  hideSourceMaps: true,

  // Disable the Sentry webpack plugin if not configured
  disableServerWebpackPlugin: !process.env.SENTRY_AUTH_TOKEN,
  disableClientWebpackPlugin: !process.env.SENTRY_AUTH_TOKEN,
}

// Apply bundle analyzer wrapper
let finalConfig = withBundleAnalyzer(nextConfig)

// Conditionally wrap with Sentry
if (process.env.NEXT_PUBLIC_SENTRY_DSN) {
  finalConfig = withSentryConfig(finalConfig, sentryWebpackPluginOptions)
}

export default finalConfig
