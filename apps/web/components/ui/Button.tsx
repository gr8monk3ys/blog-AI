import { forwardRef, type ButtonHTMLAttributes } from 'react'
import { cn } from '../../lib/cn'

// The notebook has one filled button (cta-primary, one per view) and paper-card
// buttons for everything else. Focus is the global :focus-visible outline in
// globals.css, so no ring stack here. See DESIGN.md → Components → Buttons.
export type ButtonVariant = 'default' | 'secondary' | 'outline' | 'ghost' | 'link' | 'destructive'
export type ButtonSize = 'default' | 'sm' | 'lg' | 'icon'

const VARIANT: Record<ButtonVariant, string> = {
  default: 'cta-primary rounded-xl',
  secondary: 'cta-secondary rounded-xl',
  outline: 'cta-secondary rounded-xl',
  destructive: 'cta-secondary rounded-xl text-destructive hover:text-destructive',
  ghost:
    'rounded-xl border border-transparent text-foreground hover:border-border hover:bg-card hover:text-primary',
  link: 'ink-underline h-auto px-0 text-primary',
}

const SIZE: Record<ButtonSize, string> = {
  default: 'h-10 px-4 py-2',
  sm: 'h-9 rounded-lg px-3',
  lg: 'h-12 rounded-xl px-8 text-base',
  icon: 'size-10 rounded-xl',
}

export function buttonVariants({
  variant = 'default',
  size = 'default',
  className,
}: {
  variant?: ButtonVariant
  size?: ButtonSize
  className?: string
} = {}): string {
  return cn(
    'inline-flex items-center justify-center gap-2 whitespace-nowrap text-sm font-medium transition-colors disabled:pointer-events-none disabled:opacity-50',
    VARIANT[variant],
    variant === 'link' ? undefined : SIZE[size],
    className
  )
}

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
  size?: ButtonSize
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { className, variant, size, type = 'button', ...props },
  ref
) {
  return <button ref={ref} type={type} className={buttonVariants({ variant, size, className })} {...props} />
})

export default Button
