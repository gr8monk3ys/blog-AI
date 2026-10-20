import { forwardRef, type SelectHTMLAttributes } from 'react'
import { cn } from '../../lib/cn'

// A native <select> on the field treatment. The chevron is the browser's;
// the base layer in globals.css gives the popup the page colours so Windows
// dark mode matches. See DESIGN.md → Components → Inputs / Fields.
export type SelectProps = SelectHTMLAttributes<HTMLSelectElement>

export const Select = forwardRef<HTMLSelectElement, SelectProps>(function Select(
  { className, children, ...props },
  ref
) {
  return (
    <select
      ref={ref}
      className={cn(
        'input-field flex h-10 w-full rounded-sm px-3 py-2 text-sm disabled:cursor-not-allowed disabled:opacity-50',
        className
      )}
      {...props}
    >
      {children}
    </select>
  )
})

export default Select
