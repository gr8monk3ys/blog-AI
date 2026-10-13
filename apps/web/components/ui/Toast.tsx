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

// A toast is a slip of paper card with a hairline; only the icon carries the
// signal colour (DESIGN.md → Colors → Signal). No shadow, no tinted fill.
const variantConfig: Record<ToastVariant, { icon: React.ElementType; iconColor: string }> = {
  success: { icon: CheckCircleIcon, iconColor: 'text-success' },
  error: { icon: ExclamationCircleIcon, iconColor: 'text-destructive' },
  warning: { icon: ExclamationTriangleIcon, iconColor: 'text-warning' },
  info: { icon: InformationCircleIcon, iconColor: 'text-info' },
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
          className="fixed top-4 right-4 z-50 flex items-center gap-3 px-4 py-3 rounded-lg border border-border bg-card text-card-foreground"
          role="alert"
          aria-live="polite"
        >
          <Icon
            aria-hidden="true"
            className={`w-5 h-5 shrink-0 ${config.iconColor}`}
          />
          <span className="text-sm font-medium">
            {message}
          </span>
          <button
            type="button"
            onClick={onClose}
            className="ml-2 p-1 rounded-full text-muted-foreground hover:text-primary hover:bg-muted transition-colors"
            aria-label="Dismiss notification"
          >
            <XMarkIcon className="w-4 h-4" aria-hidden="true" />
          </button>
        </m.div>
      )}
    </AnimatePresence>
  )
}
