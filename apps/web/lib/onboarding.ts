/**
 * Onboarding utilities
 *
 * Tracks whether the current user has completed the first-time
 * onboarding wizard. State is persisted in localStorage so it
 * survives page reloads but stays scoped to the device/browser.
 */

const STORAGE_KEY = 'onboarding_completed'
const COOKIE_KEY = 'onboarding_completed'
const COOKIE_MAX_AGE_SECONDS = 60 * 60 * 24 * 365

/**
 * Check whether the current user has already completed onboarding.
 *
 * Returns `true` when the flag is present in localStorage.
 * Always returns `false` on the server (SSR-safe).
 */
export function hasCompletedOnboarding(): boolean {
  if (typeof window === 'undefined') return false

  try {
    return localStorage.getItem(STORAGE_KEY) === 'true'
  } catch {
    // localStorage may be blocked (e.g. private browsing in Safari).
    return false
  }
}

/**
 * Mark onboarding as completed by writing a flag to localStorage.
 *
 * Silently fails when localStorage is unavailable so callers do not
 * need to wrap this in a try/catch.
 */
export function markOnboardingComplete(): void {
  if (typeof window === 'undefined') return

  try {
    localStorage.setItem(STORAGE_KEY, 'true')
    document.cookie = `${COOKIE_KEY}=true; path=/; max-age=${COOKIE_MAX_AGE_SECONDS}; samesite=lax`
  } catch {
    // Swallow -- quota or privacy restrictions.
  }
}

/**
 * Reset the onboarding flag so the wizard can be shown again.
 * Useful for testing or when a user explicitly wants to redo setup.
 */
export function resetOnboarding(): void {
  if (typeof window === 'undefined') return

  try {
    localStorage.removeItem(STORAGE_KEY)
    document.cookie = `${COOKIE_KEY}=; path=/; max-age=0; samesite=lax`
  } catch {
    // Swallow.
  }
}
