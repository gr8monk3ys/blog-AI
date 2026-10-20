/**
 * Join class names, dropping the falsy ones. The notebook primitives compose
 * their variants with it; no dependency, no Tailwind-merge semantics (a
 * caller who passes `className` is expected to pass non-conflicting classes).
 */
export type ClassValue = string | number | null | undefined | false

export function cn(...values: ClassValue[]): string {
  let out = ''
  for (const value of values) {
    if (!value && value !== 0) continue
    out += (out ? ' ' : '') + String(value)
  }
  return out
}
