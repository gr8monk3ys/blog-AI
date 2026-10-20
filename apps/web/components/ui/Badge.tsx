import type { HTMLAttributes } from 'react'
import { cn } from '../../lib/cn'

// The house chip is `outline`: Paper Card with a hairline, ink text, the ink
// on hover. `default` is the single filled badge for one status or count.
// Status chips are the signal tokens with their -muted wash. See DESIGN.md →
// Components → Chips / Badges.
export type BadgeVariant =
  | 'default'
  | 'secondary'
  | 'outline'
  | 'destructive'
  | 'success'
  | 'warning'
  | 'info'

const VARIANT: Record<BadgeVariant, string> = {
  default: 'border-transparent bg-primary text-primary-foreground',
  secondary: 'border-border bg-card text-foreground hover:text-primary',
  outline: 'border-border bg-card text-foreground hover:text-primary',
  destructive: 'border-transparent bg-destructive-muted text-destructive',
  success: 'border-transparent bg-success-muted text-success',
  warning: 'border-transparent bg-warning-muted text-warning',
  info: 'border-transparent bg-info-muted text-info',
}

export function badgeVariants({
  variant = 'default',
  className,
}: { variant?: BadgeVariant; className?: string } = {}): string {
  return cn(
    'inline-flex items-center rounded-full border px-3 py-1 text-xs font-semibold transition-colors',
    VARIANT[variant],
    className
  )
}

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant
}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return <span className={badgeVariants({ variant, className })} {...props} />
}

export default Badge
