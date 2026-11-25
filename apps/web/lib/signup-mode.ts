/**
 * How sign-up is gated, read in one place.
 *
 * The real gate is lib/auth.ts: any mode but `open` disables self-serve
 * email sign-up in Better Auth. The mode also tells the pages which story to
 * tell:
 *
 *   open      -- `/sign-up` renders the sign-up form; CTAs say "Start free".
 *   waitlist  -- CTAs say "Join the waitlist".
 *   invite    -- CTAs say "Sign in".
 *
 * Unknown or empty values fall back to `open`, which is today's behaviour.
 * Consumers (sign-up page, header, hero and pricing CTAs) land in the pages PR.
 */

export const SIGNUP_MODES = ['open', 'waitlist', 'invite'] as const

export type SignupMode = (typeof SIGNUP_MODES)[number]

export const DEFAULT_SIGNUP_MODE: SignupMode = 'open'

export function parseSignupMode(value: string | undefined | null): SignupMode {
  const normalised = value?.trim().toLowerCase()
  return (SIGNUP_MODES as readonly string[]).includes(normalised ?? '')
    ? (normalised as SignupMode)
    : DEFAULT_SIGNUP_MODE
}

/** Re-reads the environment on every call so tests can set it without module resets. */
export function getSignupMode(): SignupMode {
  return parseSignupMode(process.env.NEXT_PUBLIC_SIGNUP_MODE)
}
