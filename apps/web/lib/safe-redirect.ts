/** A same-origin path to return to after sign-in; anything else falls back. */
export function safeRedirectPath(value: unknown, fallback = '/generate'): string {
  return typeof value === 'string' && /^\/(?![/\\])/.test(value) ? value : fallback
}
