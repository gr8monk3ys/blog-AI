/**
 * Locale-aware display formatting.
 *
 * The UI is English (`<html lang="en">`), so formatting is pinned to en-US:
 * server and browser agree regardless of the visitor's OS locale, and
 * separators, decimals, currency and dates come from Intl instead of
 * hand-rolled toFixed()/toLocale*() calls. Formatter instances are cached.
 */
const DISPLAY_LOCALE = 'en-US'

const numberFormats = new Map<string, Intl.NumberFormat>()
const dateFormats = new Map<string, Intl.DateTimeFormat>()

function numberFormat(options: Intl.NumberFormatOptions): Intl.NumberFormat {
  const key = JSON.stringify(options)
  let format = numberFormats.get(key)
  if (!format) {
    format = new Intl.NumberFormat(DISPLAY_LOCALE, options)
    numberFormats.set(key, format)
  }
  return format
}

/** Like toFixed(digits) with grouping; omit digits for up to 3 decimals. */
export function formatNumber(value: number, fractionDigits?: number): string {
  return numberFormat(
    fractionDigits === undefined
      ? { maximumFractionDigits: 3 }
      : { minimumFractionDigits: fractionDigits, maximumFractionDigits: fractionDigits }
  ).format(value)
}

/** US-dollar amount, e.g. formatCurrency(0.0123, 4) -> "$0.0123". */
export function formatCurrency(value: number, fractionDigits = 2): string {
  return numberFormat({
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  }).format(value)
}

/** Date (or ISO string / timestamp) formatted with Intl.DateTimeFormat. */
export function formatDisplayDate(
  value: Date | string | number,
  options: Intl.DateTimeFormatOptions = { month: 'short', day: 'numeric', year: 'numeric' }
): string {
  const key = JSON.stringify(options)
  let format = dateFormats.get(key)
  if (!format) {
    format = new Intl.DateTimeFormat(DISPLAY_LOCALE, options)
    dateFormats.set(key, format)
  }
  return format.format(value instanceof Date ? value : new Date(value))
}

/** Date and time, e.g. "Sep 25, 2026, 3:04 PM". */
export function formatDisplayDateTime(value: Date | string | number): string {
  return formatDisplayDate(value, { dateStyle: 'medium', timeStyle: 'short' })
}
