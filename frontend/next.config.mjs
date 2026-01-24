/** @type {import('next').NextConfig} */
import { withSentryConfig } from '@sentry/nextjs'

const nextConfig = {
  // Recommended: Strict mode for catching issues early
  reactStrictMode: true,

  // Experimental features
  experimental: {
    // Enable scroll restoration
    scrollRestoration: true,
  },

  // Image optimization domains (add as needed)
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**.unsplash.com',
      },
    ],
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

// Conditionally wrap with Sentry
const finalConfig = process.env.NEXT_PUBLIC_SENTRY_DSN
  ? withSentryConfig(nextConfig, sentryWebpackPluginOptions)
  : nextConfig

export default finalConfig
