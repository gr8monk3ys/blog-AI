'use client'

import { Fragment, useRef, useEffect, useCallback } from 'react'
import { Dialog, Transition } from '@headlessui/react'
import { motion } from 'framer-motion'
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

const variantConfig: Record<
  ConfirmModalVariant,
  {
    icon: React.ElementType
    iconBgColor: string
    iconColor: string
    confirmButtonColor: string
    confirmButtonHoverColor: string
  }
> = {
  danger: {
    icon: ExclamationCircleIcon,
    iconBgColor: 'bg-red-100',
    iconColor: 'text-red-600',
    confirmButtonColor: 'bg-red-600',
    confirmButtonHoverColor: 'hover:bg-red-700',
  },
  warning: {
    icon: ExclamationTriangleIcon,
    iconBgColor: 'bg-amber-100',
    iconColor: 'text-amber-600',
    confirmButtonColor: 'bg-amber-600',
    confirmButtonHoverColor: 'hover:bg-amber-700',
  },
  info: {
    icon: InformationCircleIcon,
    iconBgColor: 'bg-indigo-100',
    iconColor: 'text-indigo-600',
    confirmButtonColor: 'bg-indigo-600',
    confirmButtonHoverColor: 'hover:bg-indigo-700',
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
        {/* Backdrop */}
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div
            className="fixed inset-0 bg-black/25 backdrop-blur-sm"
            aria-hidden="true"
          />
        </Transition.Child>

        {/* Modal container */}
        <div className="fixed inset-0 overflow-y-auto">
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
              <Dialog.Panel
                as={motion.div}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ duration: 0.2 }}
                className="w-full max-w-md transform overflow-hidden rounded-2xl bg-white p-6 text-left align-middle shadow-xl transition-all"
              >
                <div className="flex items-start gap-4">
                  {/* Icon */}
                  <div
                    className={`flex-shrink-0 flex items-center justify-center w-12 h-12 rounded-full ${config.iconBgColor}`}
                  >
                    <Icon
                      className={`w-6 h-6 ${config.iconColor}`}
                      aria-hidden="true"
                    />
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <Dialog.Title
                      as="h3"
                      className="text-lg font-semibold leading-6 text-gray-900"
                    >
                      {title}
                    </Dialog.Title>

                    <Dialog.Description className="mt-2 text-sm text-gray-600">
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
                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 transition-colors"
                  >
                    {cancelLabel}
                  </button>
                  <button
                    ref={confirmButtonRef}
                    type="button"
                    onClick={onConfirm}
                    className={`px-4 py-2 text-sm font-medium text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-offset-2 transition-colors ${config.confirmButtonColor} ${config.confirmButtonHoverColor} focus:ring-${variant === 'danger' ? 'red' : variant === 'warning' ? 'amber' : 'indigo'}-500`}
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
