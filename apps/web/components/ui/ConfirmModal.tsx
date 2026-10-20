'use client'

import { Fragment, useRef, useEffect, useCallback } from 'react'
import { Dialog, Transition } from '@headlessui/react'
import {
  ExclamationTriangleIcon,
  InformationCircleIcon,
  ExclamationCircleIcon,
} from '@heroicons/react/24/outline'

export type ConfirmModalVariant = 'danger' | 'warning' | 'info'

export interface ConfirmModalProps {
  isOpen: boolean
  onClose: () => void
  onConfirm: () => void
  title: string
  message: string
  confirmLabel?: string
  cancelLabel?: string
  variant?: ConfirmModalVariant
}

// The icon takes the signal colour on its -muted wash; the confirm button is
// the view's one primary button, except for a destructive confirmation, which
// is the paper-card button with Error text (DESIGN.md → Components → Buttons).
const variantConfig: Record<
  ConfirmModalVariant,
  {
    icon: React.ElementType
    iconBgColor: string
    iconColor: string
    confirmButton: string
  }
> = {
  danger: {
    icon: ExclamationCircleIcon,
    iconBgColor: 'bg-destructive-muted',
    iconColor: 'text-destructive',
    confirmButton: 'cta-secondary text-destructive hover:text-destructive',
  },
  warning: {
    icon: ExclamationTriangleIcon,
    iconBgColor: 'bg-warning-muted',
    iconColor: 'text-warning',
    confirmButton: 'cta-primary',
  },
  info: {
    icon: InformationCircleIcon,
    iconBgColor: 'bg-info-muted',
    iconColor: 'text-info',
    confirmButton: 'cta-primary',
  },
}

export default function ConfirmModal({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  variant = 'info',
}: ConfirmModalProps) {
  const confirmButtonRef = useRef<HTMLButtonElement>(null)
  const cancelButtonRef = useRef<HTMLButtonElement>(null)
  const config = variantConfig[variant]
  const Icon = config.icon

  // Handle Enter key press for confirmation
  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (event.key === 'Enter' && isOpen) {
        event.preventDefault()
        onConfirm()
      }
    },
    [isOpen, onConfirm]
  )

  useEffect(() => {
    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown)
      return () => {
        document.removeEventListener('keydown', handleKeyDown)
      }
    }
  }, [isOpen, handleKeyDown])

  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog
        as="div"
        className="relative z-50"
        onClose={onClose}
        initialFocus={cancelButtonRef}
      >
        {/* Backdrop: a modal separates with the scrim, not a shadow or a blur. */}
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 overlay-scrim" aria-hidden="true" />
        </Transition.Child>

        {/* Modal container */}
        <div className="fixed inset-0 overflow-y-auto overscroll-contain">
          <div className="flex min-h-full items-center justify-center p-4 text-center">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel className="w-full max-w-md transform overflow-hidden rounded-xl border border-border bg-popover text-popover-foreground p-6 text-left align-middle transition">
                <div className="flex items-start gap-4">
                  {/* Icon */}
                  <div
                    className={`shrink-0 flex items-center justify-center w-12 h-12 rounded-full ${config.iconBgColor}`}
                  >
                    <Icon
                      aria-hidden="true"
                      className={`w-6 h-6 ${config.iconColor}`}
                    />
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <Dialog.Title as="h3" className="text-card-title font-display">
                      {title}
                    </Dialog.Title>

                    <Dialog.Description className="mt-2 text-sm text-muted-foreground">
                      {message}
                    </Dialog.Description>
                  </div>
                </div>

                {/* Actions */}
                <div className="mt-6 flex justify-end gap-3">
                  <button
                    ref={cancelButtonRef}
                    type="button"
                    onClick={onClose}
                    className="cta-secondary rounded-lg px-4 py-2 text-sm"
                  >
                    {cancelLabel}
                  </button>
                  <button
                    ref={confirmButtonRef}
                    type="button"
                    onClick={onConfirm}
                    className={`rounded-lg px-4 py-2 text-sm ${config.confirmButton}`}
                  >
                    {confirmLabel}
                  </button>
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  )
}
