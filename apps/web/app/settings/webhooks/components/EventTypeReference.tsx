'use client'

import { useState } from 'react'
import { ChevronDownIcon, ChevronUpIcon, InformationCircleIcon } from '@heroicons/react/24/outline'
import { EVENT_TYPE_GROUPS, EVENT_TYPE_DESCRIPTIONS } from '../../../../types/webhooks'

export default function EventTypeReference() {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="mt-10">
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-2 text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 transition-colors"
      >
        <InformationCircleIcon className="w-4 h-4" />
        Event Type Reference
        {expanded ? <ChevronUpIcon className="w-3.5 h-3.5" /> : <ChevronDownIcon className="w-3.5 h-3.5" />}
      </button>

      {expanded && (
        <div className="mt-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-6 space-y-6">
          {Object.entries(EVENT_TYPE_GROUPS).map(([key, group]) => (
            <div key={key}>
              <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">{group.label} Events</h4>
              <div className="space-y-2">
                {group.types.map((type) => (
                  <div key={type} className="flex items-start gap-3">
                    <code className="text-xs font-mono px-2 py-0.5 rounded bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 shrink-0">
                      {type}
                    </code>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {EVENT_TYPE_DESCRIPTIONS[type]}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          ))}

          <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
            <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-2">Signature Verification</h4>
            <p className="text-xs text-gray-500 dark:text-gray-400 leading-relaxed">
              If you provide a signing secret, each delivery includes an{' '}
              <code className="px-1 py-0.5 rounded bg-gray-100 dark:bg-gray-700">X-Webhook-Signature</code> header
              in the format <code className="px-1 py-0.5 rounded bg-gray-100 dark:bg-gray-700">t=timestamp,v1=signature</code>.
              Verify by computing HMAC-SHA256 of <code className="px-1 py-0.5 rounded bg-gray-100 dark:bg-gray-700">{'{timestamp}.{payload}'}</code> using your secret.
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
