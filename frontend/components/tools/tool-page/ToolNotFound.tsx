'use client'

import Link from 'next/link'
import { ArrowLeftIcon } from '@heroicons/react/24/outline'

/**
 * Component displayed when a tool is not found
 */
export default function ToolNotFound() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">Tool Not Found</h1>
        <p className="text-gray-600 mb-6">
          The tool you&apos;re looking for doesn&apos;t exist or has been removed.
        </p>
        <Link
          href="/tools"
          className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
        >
          <ArrowLeftIcon className="w-4 h-4" />
          Back to Tools
        </Link>
      </div>
    </main>
  )
}
