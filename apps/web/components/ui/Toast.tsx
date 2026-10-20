'use client'

import { Fragment, useEffect } from 'react'
import { Transition } from '@headlessui/react'
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
// signal colour (DESIGN.md → Colors → Signal). No shadow, no tinted fill. It
// fades in over 200ms through Headless UI — a notification is the interface
// arriving, not content (DESIGN.md → Motion) — so framer-motion is not needed.
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
    <Transition
      show={isVisible}
      as={Fragment}
      enter="transition duration-200 ease-out"
      enterFrom="opacity-0 -translate-y-2"
      enterTo="opacity-100 translate-y-0"
      leave="transition duration-150 ease-in"
      leaveFrom="opacity-100 translate-y-0"
      leaveTo="opacity-0 -translate-y-2"
    >
      <div
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
      </div>
    </Transition>
  )
}
