'use client'

import { useState, useCallback } from 'react'
import Toast, { ToastVariant, ToastProps } from '../components/ui/Toast'

export interface ToastOptions {
  message: string
  variant?: ToastVariant
  duration?: number
}

interface ToastState {
  isVisible: boolean
  message: string
  variant: ToastVariant
  duration: number
}

/**
 * A hook that provides an imperative API for showing toast notifications.
 *
 * @example
 * ```tsx
 * function MyComponent() {
 *   const { showToast, ToastComponent } = useToast()
 *
 *   const handleSave = async () => {
 *     try {
 *       await saveData()
 *       showToast({ message: 'Saved successfully!', variant: 'success' })
 *     } catch (error) {
 *       showToast({ message: 'Failed to save.', variant: 'error' })
 *     }
 *   }
 *
 *   return (
 *     <>
 *       <button onClick={handleSave}>Save</button>
 *       <ToastComponent />
 *     </>
 *   )
 * }
 * ```
 */
export function useToast() {
  const [state, setState] = useState<ToastState>({
    isVisible: false,
    message: '',
    variant: 'info',
    duration: 3000,
  })

  const showToast = useCallback((options: ToastOptions) => {
    setState({
      isVisible: true,
      message: options.message,
      variant: options.variant || 'info',
      duration: options.duration ?? 3000,
    })
  }, [])

  const hideToast = useCallback(() => {
    setState((prev) => ({ ...prev, isVisible: false }))
  }, [])

  const ToastComponent = useCallback(
    () => (
      <Toast
        isVisible={state.isVisible}
        message={state.message}
        variant={state.variant}
        duration={state.duration}
        onClose={hideToast}
      />
    ),
    [state.isVisible, state.message, state.variant, state.duration, hideToast]
  )

  return {
    showToast,
    hideToast,
    ToastComponent,
  }
}

export default useToast
