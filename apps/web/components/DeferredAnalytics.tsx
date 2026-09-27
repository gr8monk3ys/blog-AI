'use client'

import dynamic from 'next/dynamic'

// Analytics and Speed Insights never affect what the user sees, so they load
// after hydration instead of riding in the initial bundle.
const Analytics = dynamic(() => import('@vercel/analytics/react').then((m) => m.Analytics), {
  ssr: false,
})
const SpeedInsights = dynamic(
  () => import('@vercel/speed-insights/next').then((m) => m.SpeedInsights),
  { ssr: false }
)

export default function DeferredAnalytics() {
  return (
    <>
      <Analytics />
      <SpeedInsights />
    </>
  )
}
