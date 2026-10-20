import { forwardRef, type InputHTMLAttributes } from 'react'
import { cn } from '../../lib/cn'

// Field (`input-field`): Paper Card fill, hairline, 8px radius, 40px tall.
// Focus warms the border to the ink at 50% plus the global outline; an
// `aria-invalid` field takes an Error border. See DESIGN.md → Components →
// Inputs / Fields.
export const inputClassName =
  'input-field flex h-10 w-full rounded-sm px-3 py-2 text-sm disabled:cursor-not-allowed disabled:opacity-50'

export type InputProps = InputHTMLAttributes<HTMLInputElement>

export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  { className, type = 'text', ...props },
  ref
) {
  return <input ref={ref} type={type} className={cn(inputClassName, className)} {...props} />
})

export default Input
