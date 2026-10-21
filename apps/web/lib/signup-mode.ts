/**
 * How sign-up is gated, read in one place.
 *
 * Clerk owns identity, so the real gate is Clerk's dashboard setting
 * (Restricted / Waitlist mode). This flag only tells the pages which story to
 * tell so the surface and the dashboard agree:
 *
 *   open      -- `/sign-up` renders <SignUp>; CTAs say "Start free".
 *   waitlist  -- `/sign-up` renders Clerk's <Waitlist>; CTAs say "Join the waitlist".
 *   invite    -- `/sign-up` shows an invitation notice (still <SignUp> when
 *                `__clerk_ticket` is in the query); CTAs say "Sign in".
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
