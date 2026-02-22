'use client'

import { useEffect } from 'react'
import { m, AnimatePresence } from 'framer-motion'
import {
  CheckCircleIcon,
  ExclamationCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline'

export type ToastVariant = 'success' | 'error' | 'warning' | 'info'

export interface ToastProps {
  isVisible: boolean
  message: string
  variant?: ToastVariant
  duration?: number
  onClose: () => void
}

const variantConfig: Record<
  ToastVariant,
  {
    icon: React.ElementType
    bgColor: string
    borderColor: string
    textColor: string
    iconColor: string
  }
> = {
  success: {
    icon: CheckCircleIcon,
    bgColor: 'bg-emerald-50 dark:bg-emerald-950/30',
    borderColor: 'border-emerald-200 dark:border-emerald-800',
    textColor: 'text-emerald-800 dark:text-emerald-300',
    iconColor: 'text-emerald-500',
  },
  error: {
    icon: ExclamationCircleIcon,
    bgColor: 'bg-red-50 dark:bg-red-950/30',
    borderColor: 'border-red-200 dark:border-red-800',
    textColor: 'text-red-800 dark:text-red-300',
    iconColor: 'text-red-500',
  },
  warning: {
    icon: ExclamationTriangleIcon,
    bgColor: 'bg-amber-50 dark:bg-amber-950/30',
    borderColor: 'border-amber-200 dark:border-amber-800',
    textColor: 'text-amber-800 dark:text-amber-300',
    iconColor: 'text-amber-500',
  },
  info: {
    icon: InformationCircleIcon,
    bgColor: 'bg-amber-50 dark:bg-amber-950/30',
    borderColor: 'border-amber-200 dark:border-amber-800',
    textColor: 'text-amber-800 dark:text-amber-300',
    iconColor: 'text-amber-500',
  },
}

export default function Toast({
  isVisible,
  message,
  variant = 'info',
  duration = 3000,
  onClose,
}: ToastProps) {
  const config = variantConfig[variant]
  const Icon = config.icon

  useEffect(() => {
    if (isVisible && duration > 0) {
      const timer = setTimeout(() => {
        onClose()
      }, duration)
      return () => clearTimeout(timer)
    }
  }, [isVisible, duration, onClose])

  return (
    <AnimatePresence>
      {isVisible && (
        <m.div
          initial={{ opacity: 0, y: -20, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -20, scale: 0.95 }}
          transition={{ duration: 0.2, ease: 'easeOut' }}
          className={`fixed top-4 right-4 z-50 flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg border ${config.bgColor} ${config.borderColor}`}
          role="alert"
          aria-live="polite"
        >
          <Icon
            className={`w-5 h-5 flex-shrink-0 ${config.iconColor}`}
            aria-hidden="true"
          />
          <span className={`text-sm font-medium ${config.textColor}`}>
            {message}
          </span>
          <button
            type="button"
            onClick={onClose}
            className={`ml-2 p-1 rounded-full hover:bg-black/5 dark:hover:bg-white/10 transition-colors ${config.textColor}`}
            aria-label="Dismiss notification"
          >
            <XMarkIcon className="w-4 h-4" aria-hidden="true" />
          </button>
        </m.div>
      )}
    </AnimatePresence>
  )
}
