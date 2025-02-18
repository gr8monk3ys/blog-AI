'use client'

import { useState, useCallback, useRef } from 'react'
import ConfirmModal, {
  ConfirmModalVariant,
} from '../components/ui/ConfirmModal'

export interface ConfirmOptions {
  title: string
  message: string
  confirmLabel?: string
  cancelLabel?: string
  variant?: ConfirmModalVariant
}

interface ConfirmState extends ConfirmOptions {
  isOpen: boolean
}

type ConfirmResolver = (value: boolean) => void

/**
 * A hook that provides an imperative API for showing confirm modals.
 *
 * @example
 * ```tsx
 * function MyComponent() {
 *   const { confirm, ConfirmModalComponent } = useConfirmModal()
 *
 *   const handleDelete = async () => {
 *     const confirmed = await confirm({
 *       title: 'Delete item?',
 *       message: 'This action cannot be undone.',
 *       variant: 'danger',
 *       confirmLabel: 'Delete',
 *     })
 *
 *     if (confirmed) {
 *       // Perform deletion
 *     }
 *   }
 *
 *   return (
 *     <>
 *       <button onClick={handleDelete}>Delete</button>
 *       <ConfirmModalComponent />
 *     </>
 *   )
 * }
 * ```
 */
export function useConfirmModal() {
  const [state, setState] = useState<ConfirmState>({
    isOpen: false,
    title: '',
    message: '',
  })

  const resolverRef = useRef<ConfirmResolver | null>(null)

  const confirm = useCallback((options: ConfirmOptions): Promise<boolean> => {
    return new Promise<boolean>((resolve) => {
      resolverRef.current = resolve
      setState({
        isOpen: true,
        ...options,
      })
    })
  }, [])

  const handleClose = useCallback(() => {
    setState((prev) => ({ ...prev, isOpen: false }))
    if (resolverRef.current) {
      resolverRef.current(false)
      resolverRef.current = null
    }
  }, [])

  const handleConfirm = useCallback(() => {
    setState((prev) => ({ ...prev, isOpen: false }))
    if (resolverRef.current) {
      resolverRef.current(true)
      resolverRef.current = null
    }
  }, [])

  const ConfirmModalComponent = useCallback(
    () => (
      <ConfirmModal
        isOpen={state.isOpen}
        onClose={handleClose}
        onConfirm={handleConfirm}
        title={state.title}
        message={state.message}
        confirmLabel={state.confirmLabel}
        cancelLabel={state.cancelLabel}
        variant={state.variant}
      />
    ),
    [
      state.isOpen,
      state.title,
      state.message,
      state.confirmLabel,
      state.cancelLabel,
      state.variant,
      handleClose,
      handleConfirm,
    ]
  )

  return {
    confirm,
    ConfirmModalComponent,
  }
}

export default useConfirmModal
