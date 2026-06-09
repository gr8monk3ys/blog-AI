'use client'

import Link from 'next/link'
import { m } from 'framer-motion'

/**
 * Presentational banner sections for the bulk generation page, extracted from
 * BulkGenerationPageClient as part of the Phase 3.1 split
 * (docs/REMEDIATION_PLAN.md). Behavior pinned by
 * tests/app/bulk/BulkGenerationPageClient.test.tsx.
 */

export function BulkHero() {
  return (
    <section className="bg-gradient-to-r from-amber-600 to-amber-700 text-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <m.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <h1 className="text-2xl sm:text-3xl font-bold mb-2">
            Bulk SEO Content Workflow
          </h1>
          <p className="text-amber-100">
            Queue multiple topics, compare provider cost, and generate campaign-ready drafts
            faster than prompt-by-prompt writing.
          </p>
          <div className="mt-4 flex flex-wrap gap-3 text-sm">
            <span className="rounded-full bg-white/15 px-3 py-1">Best for publishing calendars</span>
            <span className="rounded-full bg-white/15 px-3 py-1">Pairs with Brand Voice</span>
            <span className="rounded-full bg-white/15 px-3 py-1">Strongest Pro workflow today</span>
          </div>
        </m.div>
      </div>
    </section>
  )
}

export function ActivationHint({
  hint,
  onDismiss,
}: {
  hint: string
  onDismiss: () => void
}) {
  return (
    <m.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="mb-6 rounded-2xl border border-green-200 bg-green-50/80 p-5 text-sm text-green-900 dark:border-green-900/40 dark:bg-green-950/30 dark:text-green-100"
    >
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <p>{hint}</p>
        <button
          type="button"
          onClick={onDismiss}
          className="rounded-lg border border-green-300 px-3 py-2 font-medium text-green-800 transition-colors hover:bg-green-100 dark:border-green-800 dark:text-green-200 dark:hover:bg-green-900/30"
        >
          Dismiss
        </button>
      </div>
    </m.div>
  )
}

export function WorkflowBanner() {
  return (
    <m.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.05 }}
      className="mb-6 rounded-2xl border border-amber-200 bg-amber-50/80 p-5 text-sm text-amber-900 dark:border-amber-900/40 dark:bg-amber-950/30 dark:text-amber-100"
    >
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p className="font-semibold">Recommended workflow</p>
          <p className="mt-1 text-amber-800 dark:text-amber-200">
            Create a brand profile first, then use bulk generation for repeatable SEO content
            batches. That is the clearest upgrade path from free usage to a paid workflow.
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <Link
            href="/brand"
            className="inline-flex items-center justify-center rounded-lg bg-amber-600 px-4 py-2 font-medium text-white transition-colors hover:bg-amber-700"
          >
            Open Brand Voice
          </Link>
          <Link
            href="/pricing"
            className="inline-flex items-center justify-center rounded-lg border border-amber-300 px-4 py-2 font-medium text-amber-800 transition-colors hover:bg-amber-100 dark:border-amber-800 dark:text-amber-200 dark:hover:bg-amber-900/30"
          >
            Compare Plans
          </Link>
        </div>
      </div>
    </m.div>
  )
}
