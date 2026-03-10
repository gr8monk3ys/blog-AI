'use client'

import { motion } from 'framer-motion'
import { CheckIcon } from '@heroicons/react/24/outline'
import type { ToastState } from './types'

interface ToastNotificationProps {
  toast: ToastState
}

/**
 * Toast notification component for displaying success/error messages
 */
export default function ToastNotification({ toast }: ToastNotificationProps) {
  if (!toast.show) {
    return null
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="fixed top-4 right-4 z-50"
    >
      <div
        className={`flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg ${
          toast.type === 'success'
            ? 'bg-emerald-50 border border-emerald-200 text-emerald-800'
            : 'bg-red-50 border border-red-200 text-red-800'
        }`}
      >
        {toast.type === 'success' ? (
          <CheckIcon className="w-5 h-5 text-emerald-500" />
        ) : (
          <svg
            className="w-5 h-5 text-red-500"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        )}
        <span className="text-sm font-medium">{toast.message}</span>
      </div>
    </motion.div>
  )
}
