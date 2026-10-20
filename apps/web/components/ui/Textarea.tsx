import { forwardRef, type TextareaHTMLAttributes } from 'react'
import { cn } from '../../lib/cn'

// The field, grown: same `input-field` treatment as Input with a minimum
// height for prose. See DESIGN.md → Components → Inputs / Fields.
export type TextareaProps = TextareaHTMLAttributes<HTMLTextAreaElement>

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(function Textarea(
  { className, ...props },
  ref
) {
  return (
    <textarea
      ref={ref}
      className={cn(
        'input-field flex min-h-20 w-full rounded-sm px-3 py-2 text-sm leading-relaxed disabled:cursor-not-allowed disabled:opacity-50',
        className
      )}
      {...props}
    />
  )
})

export default Textarea
